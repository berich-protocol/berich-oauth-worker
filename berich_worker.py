#!/usr/bin/env python3
"""BeRich 閒置 AI 訂閱額度共享節點 (Cross-Platform OAuth Subscription Worker).

把電腦上閒置的 AI 月費訂閱額度（免 API Key）透過本機官方 CLI 分享給社群，已登入之會員在節點保持在線期間享有 BeRich 台股盤中 VIP 與跨模型互助額度（可調用當前在線模型）。
支援跨平台（macOS / Windows）與官方 CLI 登入：
1. claude_code: 透過 `claude auth login` 共享 Claude Pro / Max 閒置額度（加上 --tools "" 停用工具）
2. codex: 透過 `codex login` 共享 ChatGPT Plus / Pro 閒置額度（指定 read-only 與 ephemeral 參數）
3. gemini_cli: 透過 `gemini` 共享 Google AI (Gemini) 閒置額度（指定 sandbox 與 plan 模式）

運行機制、資安架構與限制聲明：
1. 全對話內容點對點與記憶體加密 (br_enc_v1 AEAD)：
   - 傳輸層與會話層雙重加密：網關派發任務（/api/compute/tasks/claim 之 prompt 完整多輪上下文）與 Worker 提交結果（/api/compute/tasks/submit 之 result）全程採用 100% Python 標準庫實作之 br_enc_v1 認證加密封裝（HKDF-SHA256 金鑰衍生 + 128-bit 隨機 Nonce + SHA256-CTR 對稱加密 + HMAC-SHA256 Encrypt-then-MAC 完整性標籤，並綁定 berich-e2ee-v1|{direction}|{task_id}|{node_id} 關聯資料 AAD），防範跨任務重放與中間人竄改。
   - 伺服器 RAM 密文封裝與即時銷毀 (Zeroization)：調度佇列於伺服器記憶體中亦以獨立金鑰加密保存，且在推論完成並回傳呼叫端的瞬間立即從記憶體佇列抹除（零資料庫落盤、零對話日誌留存）。
   - 本機零歷史與防注入加固：Worker 強制驗證模型參數白名單（阻擋 -- 旗標注入）、注入 HISTFILE=/dev/null 等零歷史環境變數，且絕不在終端機或錯誤日誌印出對話明文或 OAuth 憑證。
2. 本機 CLI 調用與授權傳輸：Worker 透過本機已登入之官方 CLI 轉發推論。官方 CLI 運行時仍會讀取其本機登入憑證與設定，請求會經過調度服務與官方上游伺服器。程式透過指定空白暫存目錄與停用工具參數降低風險，但不等於完整系統沙盒隔離，亦不保證無本機檔案讀取。
3. 前置閒置檢查機制 (Idle Guard)：閒置避讓為選用參數（網頁指令預設帶入 --idle-only，預設閾值為 60 秒 --idle-threshold 60.0）。啟用時，Worker 於任務領取前與呼叫 CLI 前雙重檢查系統閒置狀態；偵測失敗或使用者活躍時停止領單。若 CLI 已在執行中，移動滑鼠或鍵盤不會即時強制殺死進行中的 CLI 行程；待當前任務完成後，若偵測到使用者正在操作電腦，才會暫停領取新任務。若未加上 --idle-only，Worker 將處於全時段接單狀態。
4. 跨平台閒置偵測差異：macOS 與 Windows 支援原生閒置讀取；Linux 系統目前閒置偵測回傳 None，若於 Linux 啟用 --idle-only 將因安全保護機制而無法領單，Linux 不支援完整閒置避讓模式。
5. 服務端用量推估機制：服務端後端維持 5 小時滾動用量推估，用於社群池容量調度並設有 75% 軟上限保護，非本機 Worker 直接追蹤官方額度。此數值為服務端推估，無法查詢官方後端真實剩餘額度，亦不保證保留 25% 官方額度。
6. 關鍵字過濾與脫敏局限：內建關鍵字過濾與正規表達式脫敏僅為輔助過濾手段，無法保證絕對安全、不保證完全去識別化。
7. 服務條款與無封號保證 (No Ban Guarantee)：本專案為開源分散式運算技術實作，無法保證零封號風險。各 AI 供應商隨時可能更新服務條款，使用者須自行評估並承擔使用帳號之相關風險。
"""

import argparse
import base64
import ctypes
import hashlib
import hmac
import json
import logging
import os
import platform
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

MAX_PROMPT_CHARS = 32_000
MAX_OUTPUT_CHARS = 64_000
MAX_HTTP_RESPONSE_BYTES = 2 * 1024 * 1024
ENC_ENVELOPE_PREFIX = "br_enc_v1:"

# 嚴格限制模型名稱格式（禁止以 - 開頭或夾帶空白/特殊字元，防止 CLI 參數注入與 Shell 注入）
SAFE_MODEL_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,63}$")

# 確保 Windows PowerShell / CMD 終端機輸出繁體中文與符號不發生 cp950 編碼崩潰
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("berich_node")

# 關鍵詞與指令過濾（降低惡意 Prompt、機密竊取或違反服務條款指令之執行風險）
DANGEROUS_PATTERNS = [
    re.compile(r"(rm\s+-rf|chmod|chown|killall|reboot|shutdown|del\s+/f|format\s+c:)", re.I),
    re.compile(r"(cat\s+~/.ssh|cat\s+/etc/shadow|id_rsa|\.aws/credentials|\.claude|\.codex|\.gemini|\.env\b)", re.I),
    re.compile(r"(curl\s+.*\|\s*bash|wget\s+.*\|\s*sh|Invoke-Expression|powershell\s+-enc)", re.I),
    re.compile(r"(ignore\s+all\s+previous\s+(safety\s+)?instructions|how\s+to\s+make\s+a\s+bomb|write\s+ransomware|ransomware\s+payload|seed\s+phrase|mnemonic\s+phrase)", re.I),
]

# 個資與金鑰格式脫敏規則（相容中英混排，降低 API Key / 私鑰 / OAuth Token / JWT / Email 格式傳入之風險）
PII_REDACTION_RULES = [
    (re.compile(r"(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{16,}(?![A-Za-z0-9_-])"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?<![A-Za-z0-9_])AIza[0-9A-Za-z_-]{35}(?![0-9A-Za-z_-])"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?<![A-Za-z0-9_])(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{24,}(?![A-Za-z0-9_])"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?<![A-Za-z0-9_])AKIA[0-9A-Z]{16}(?![0-9A-Z])"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?<![A-Za-z0-9_])bw_oauth_[a-fA-F0-9_]{12,}(?![a-fA-F0-9_])"), "[REDACTED_OAUTH_TOKEN]"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "[REDACTED_JWT_TOKEN]"),
    (re.compile(r"(?<![A-Za-z0-9_])0x[a-fA-F0-9]{64}(?![a-fA-F0-9])"), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?<!\d)09\d{2}[-\s]?\d{3}[-\s]?\d{3}(?!\d)"), "[REDACTED_PHONE]"),
]

# AI 訂閱額度用罄 / 速率限制 / 授權失效偵測規則（觸發時自動將任務平滑轉交給下一位使用者的節點）
AUTH_ERROR_REGEX = re.compile(
    r"(not\s+logged\s+in|login\s+required|please\s+run\s+claude\s+(?:auth\s+)?login|"
    r"unauthorized|authentication\s+failed|invalid\s+api\s+key|session\s+expired)",
    re.I,
)
RPM_LIMIT_REGEX = re.compile(
    r"(requests\s+per\s+minute|\brpm\b|slow\s+down|retry\s+after\s+\d+\s*s)",
    re.I,
)
QUOTA_EXHAUSTED_REGEX = re.compile(
    r"(rate[\s_-]*limit|quota[\s_-]*exceeded|usage[\s_-]*limit|too\s+many\s+requests|"
    r"status\s*429|http\s*429|limit\s+reached|resets\s+at|out\s+of\s+credits|quota_exhausted)",
    re.I,
)


def derive_node_session_secret(node_id: str, oauth_token: Optional[str] = None) -> str:
    """衍生節點專屬之端對端會話加密主金鑰（優先綁定 OAuth 憑證，無憑證時退回節點 ID 衍生）。"""
    clean_token = (oauth_token or "").strip()
    if clean_token:
        return f"berich-oauth-key:{clean_token}"
    return f"berich-node-key:{(node_id or '').strip()}"


def _xor_keystream(data: bytes, enc_key: bytes, nonce: bytes) -> bytes:
    """使用 HMAC-SHA256 計數器模式 (CTR) 產生密碼學金鑰流並進行對稱加解密（100% Python 標準庫）。"""
    out = bytearray(len(data))
    block_count = (len(data) + 31) // 32
    for counter in range(block_count):
        keystream_block = hmac.new(
            enc_key,
            nonce + counter.to_bytes(8, "big"),
            hashlib.sha256,
        ).digest()
        offset = counter * 32
        chunk = data[offset : offset + 32]
        for idx, b_val in enumerate(chunk):
            out[offset + idx] = b_val ^ keystream_block[idx]
    return bytes(out)


def encrypt_conversation_payload(
    plaintext: str,
    secret_key: str,
    task_id: str,
    node_id: str,
    direction: str = "claim",
) -> str:
    """將完整對話內容（含多輪上下文 Prompt 與推論回應 Result）進行 AEAD 認證加密 (Encrypt-then-MAC)。

    採用 HKDF-SHA256 金鑰衍生 + 128-bit 隨機 Nonce + SHA256-CTR + HMAC-SHA256 完整性防竄改標籤，
    將關聯資料 AAD (direction | task_id | node_id) 綁定至密文，杜絕跨任務重放或中間人竄改。
    格式：br_enc_v1:<nonce_hex>:<ciphertext_b64>:<hmac_hex>
    """
    raw_bytes = (plaintext or "").encode("utf-8")
    nonce = secrets.token_bytes(16)
    aad = f"berich-e2ee-v1|{direction}|{task_id}|{node_id}".encode("utf-8")
    key_bytes = (secret_key or "berich-default").encode("utf-8")

    # HKDF-Extract & Expand
    prk = hmac.new(nonce, key_bytes, hashlib.sha256).digest()
    enc_key = hmac.new(prk, b"enc|" + aad + b"\x01", hashlib.sha256).digest()
    mac_key = hmac.new(prk, b"mac|" + aad + b"\x02", hashlib.sha256).digest()

    ciphertext = _xor_keystream(raw_bytes, enc_key, nonce)
    tag = hmac.new(mac_key, aad + b"|" + nonce + ciphertext, hashlib.sha256).hexdigest()
    ct_b64 = base64.urlsafe_b64encode(ciphertext).decode("ascii")
    return f"{ENC_ENVELOPE_PREFIX}{nonce.hex()}:{ct_b64}:{tag}"


def decrypt_conversation_payload(
    envelope: str,
    secret_key: str,
    task_id: str,
    node_id: str,
    direction: str = "claim",
) -> str:
    """驗證 HMAC 簽章與 AAD 綁定後解密對話內容；若遭竄改、偽造或跨節點重放則立即拋出 ValueError。"""
    if not isinstance(envelope, str) or not envelope.startswith(ENC_ENVELOPE_PREFIX):
        raise ValueError("Missing or invalid encryption envelope prefix (expected br_enc_v1:)")
    parts = envelope.split(":")
    if len(parts) != 4 or parts[0] != "br_enc_v1":
        raise ValueError("Malformed br_enc_v1 envelope structure")
    _, nonce_hex, ct_b64, provided_tag = parts
    if len(nonce_hex) != 32 or len(provided_tag) != 64:
        raise ValueError("Invalid nonce or HMAC tag length")
    try:
        nonce = bytes.fromhex(nonce_hex)
        ciphertext = base64.urlsafe_b64decode(ct_b64.encode("ascii"))
    except Exception as exc:
        raise ValueError("Invalid hex/base64 encoding in encrypted payload") from exc

    aad = f"berich-e2ee-v1|{direction}|{task_id}|{node_id}".encode("utf-8")
    key_bytes = (secret_key or "berich-default").encode("utf-8")

    prk = hmac.new(nonce, key_bytes, hashlib.sha256).digest()
    enc_key = hmac.new(prk, b"enc|" + aad + b"\x01", hashlib.sha256).digest()
    mac_key = hmac.new(prk, b"mac|" + aad + b"\x02", hashlib.sha256).digest()

    expected_tag = hmac.new(mac_key, aad + b"|" + nonce + ciphertext, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_tag, provided_tag):
        raise ValueError("HMAC authentication failed: conversation payload tampered or key mismatch")

    plaintext_bytes = _xor_keystream(ciphertext, enc_key, nonce)
    return plaintext_bytes.decode("utf-8")


def is_valid_model_name(model: str) -> bool:
    """驗證模型識別碼是否安全（禁止以 `-` 開頭或包含特殊字元，防止 CLI 旗標注入）。"""
    return bool(model and isinstance(model, str) and SAFE_MODEL_REGEX.match(model))


def _get_anonymous_host_hash() -> str:
    """將本機電腦名稱轉為不可逆之 8 碼匿名雜湊，防止外洩號主真實姓名。"""
    raw = f"{platform.system()}-{platform.machine()}-{socket.gethostname()}"
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:8]


def is_quota_exhausted_output(text: str) -> bool:
    """檢查 CLI 輸出是否代表該使用者的 AI 訂閱配額已達上限 (429 / Usage Limit)。"""
    return bool(text and QUOTA_EXHAUSTED_REGEX.search(text))


def classify_cli_error(text: str, provider: str) -> Optional[str]:
    """精細分類 CLI 異常輸出：區分未登入 (AUTH_REQUIRED)、短暫每分鐘限流 (RATE_LIMITED_RPM) 與 5 小時配額用罄 (QUOTA_EXHAUSTED)。"""
    if not text:
        return None
    if AUTH_ERROR_REGEX.search(text):
        return f"__ERROR__:AUTH_REQUIRED:{provider}"
    if RPM_LIMIT_REGEX.search(text):
        return f"__ERROR__:RATE_LIMITED_RPM:{provider}"
    if QUOTA_EXHAUSTED_REGEX.search(text):
        return f"__QUOTA_EXHAUSTED__:{provider}"
    return None


def redact_sensitive_pii(text: str) -> str:
    """自動將文字中可能夾帶的 API Key、私鑰與 Email 遮罩脫敏。"""
    cleaned = text or ""
    for regex, replacement in PII_REDACTION_RULES:
        cleaned = regex.sub(replacement, cleaned)
    return cleaned


def sanitize_prompt(prompt: str) -> Tuple[bool, str]:
    """檢查提示詞長度、是否包含特定指令特徵，並執行個資格式脫敏。"""
    if not isinstance(prompt, str) or not prompt.strip():
        return False, "空的提示詞。"
    if "\x00" in prompt:
        return False, "偵測到非法 Null Byte 字元，拒絕執行。"
    if len(prompt) > MAX_PROMPT_CHARS:
        return False, f"提示詞長度超過安全上限 ({MAX_PROMPT_CHARS} 字元)，拒絕執行。"
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(prompt):
            return False, f"偵測到高風險惡意指令模式 ({pattern.pattern})，拒絕執行。"
    return True, redact_sensitive_pii(prompt)


def get_system_idle_seconds() -> Optional[float]:
    """取得系統滑鼠/鍵盤閒置秒數（支援 macOS 與 Windows，不使用 shell=True）。若無法偵測則回傳 None。"""
    sys_name = platform.system()
    if sys_name == "Darwin":
        try:
            out = subprocess.check_output(
                ["/usr/sbin/ioreg", "-c", "IOHIDSystem", "-d", "4"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=3.0,
            )
            match = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', out)
            if match:
                return float(int(match.group(1)) // 1_000_000_000)
            return None
        except Exception:
            return None
    elif sys_name == "Windows":
        try:
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                return max(0.0, float(millis) / 1000.0)
        except Exception:
            return None
    return None


class LocalCLIBridge:
    """本機 OAuth 訂閱 CLI 橋接器（支援 macOS / Windows，透過空白臨時目錄與參數限制降低風險）。"""

    @staticmethod
    def _find_bin(name: str) -> Optional[str]:
        """跨平台尋找執行檔（在 Windows 自動嘗試 .cmd / .exe / .bat）。"""
        found = shutil.which(name)
        if found:
            return found
        if platform.system() == "Windows":
            for ext in (".cmd", ".exe", ".bat"):
                f_ext = shutil.which(name + ext)
                if f_ext:
                    return f_ext
        return None

    @classmethod
    def detect_available_clis(cls) -> Dict[str, str]:
        """偵測本機已安裝之 AI 訂閱 CLI 工具。"""
        tools = {}
        claude_path = cls._find_bin("claude")
        if claude_path:
            tools["claude_code"] = claude_path
        codex_path = cls._find_bin("codex")
        if codex_path:
            tools["codex"] = codex_path
        gemini_path = cls._find_bin("gemini")
        if gemini_path:
            tools["gemini_cli"] = gemini_path
        return tools

    @classmethod
    def trigger_subscription_oauth_login(cls, provider_type: str) -> bool:
        """引導並觸發本機 AI 訂閱 CLI 之官方 OAuth 瀏覽器授權登入。"""
        is_win = platform.system() == "Windows"
        if provider_type == "claude_code":
            bin_path = cls._find_bin("claude")
            if not bin_path:
                logger.warning("尚未安裝 Claude Code CLI！請先執行: npm install -g @anthropic-ai/claude-code")
                return False
            logger.info("🔑 正在啟動 Anthropic Claude 官方 OAuth 瀏覽器授權登入 (claude auth login)...")
            use_shell = is_win and bin_path.lower().endswith((".cmd", ".bat"))
            subprocess.run([bin_path, "auth", "login"], shell=use_shell, timeout=300.0)
            return True
        elif provider_type == "codex":
            bin_path = cls._find_bin("codex")
            if not bin_path:
                logger.warning("尚未安裝 OpenAI Codex CLI！請先執行: npm install -g @openai/codex")
                return False
            logger.info("🔑 正在啟動 OpenAI ChatGPT Plus/Pro 官方 OAuth 瀏覽器授權登入 (codex login)...")
            use_shell = is_win and bin_path.lower().endswith((".cmd", ".bat"))
            subprocess.run([bin_path, "login"], shell=use_shell, timeout=300.0)
            return True
        elif provider_type == "gemini_cli":
            bin_path = cls._find_bin("gemini")
            if not bin_path:
                logger.warning("尚未安裝 Google Gemini CLI！請先執行: npm install -g @google/gemini-cli")
                return False
            logger.info("🔑 正在啟動 Google Gemini 官方 OAuth 瀏覽器授權登入 (啟動後請選擇 Sign in with Google)...")
            use_shell = is_win and bin_path.lower().endswith((".cmd", ".bat"))
            subprocess.run([bin_path], shell=use_shell, timeout=300.0)
            return True
        return True

    @staticmethod
    def _build_sanitized_env(isolated_cwd: str) -> Dict[str, str]:
        """建立最小化環境變數：移除付費 API Key 等變數，並強制關閉本機歷史紀錄與外部遙測。"""
        allowed_keys = {
            "PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LC_ALL", "TERM",
            "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "SYSTEMROOT",
            "WINDIR", "COMSPEC", "PATHEXT", "HOMEDRIVE", "HOMEPATH",
            "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME",
        }
        clean_env: Dict[str, str] = {}
        for k, v in os.environ.items():
            if k.upper() in allowed_keys:
                clean_env[k] = v
        clean_env["TMPDIR"] = isolated_cwd
        clean_env["TEMP"] = isolated_cwd
        clean_env["TMP"] = isolated_cwd
        clean_env["CLAUDE_CODE_SAFE_MODE"] = "1"
        clean_env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
        clean_env["HISTFILE"] = "/dev/null"
        clean_env["HISTSIZE"] = "0"
        clean_env["SAVEHIST"] = "0"
        clean_env["NODE_REPL_HISTORY"] = ""
        clean_env["PYTHONHISTFILE"] = "/dev/null"
        clean_env["DO_NOT_TRACK"] = "1"
        clean_env["ANONYMIZED_TELEMETRY"] = "false"
        clean_env["CI"] = "true"
        return clean_env

    @classmethod
    def _run_sandboxed_cli(
        cls,
        cmd: List[str],
        clean_prompt: str,
        provider: str,
        timeout: float,
    ) -> Tuple[str, int]:
        """於每次獨立建立之空白 TemporaryDirectory 中執行 CLI，透過 stdin 傳入 Prompt 降低參數注入與環境變數展開風險。"""
        try:
            with tempfile.TemporaryDirectory(prefix="berich_sbx_") as isolated_cwd:
                sanitized_env = cls._build_sanitized_env(isolated_cwd)
                res = subprocess.run(
                    cmd,
                    input=clean_prompt,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                    cwd=isolated_cwd,
                    env=sanitized_env,
                    shell=(platform.system() == "Windows" and cmd[0].lower().endswith((".cmd", ".bat"))),
                )
            combined_out = f"{res.stdout or ''}\n{res.stderr or ''}".strip()
            err_tag = classify_cli_error(combined_out, provider)
            if err_tag:
                return err_tag, 0
            if res.returncode != 0:
                logger.warning("%s CLI 執行異常 (exit_code=%s)，已省略原始錯誤輸出以保護對話隱私", provider, res.returncode)
                return f"__ERROR__:AUTH_REQUIRED:{provider}", 0

            raw_output = (res.stdout or "").strip()
            if not raw_output and provider in ("codex", "gemini_cli"):
                return f"__ERROR__:AUTH_REQUIRED:{provider}", 0
            output = redact_sensitive_pii(raw_output[:MAX_OUTPUT_CHARS])
            token_count = max(50, len(clean_prompt) // 2 + len(output) // 2)
            return output, token_count
        except subprocess.TimeoutExpired:
            return f"__QUOTA_EXHAUSTED__:{provider}", 0
        except Exception:
            logger.warning("%s CLI 呼叫失敗，已省略異常細節以保護對話隱私", provider)
            return f"__ERROR__:AUTH_REQUIRED:{provider}", 0

    @classmethod
    def execute_claude_code(cls, prompt: str, model: str = "default", timeout: float = 60.0) -> Tuple[str, int]:
        """調用本機 OAuth 授權之 Claude Code CLI（停用工具 + plan 權限模式 + 獨立目錄執行）。"""
        if model and not is_valid_model_name(model):
            return "__ERROR__:INVALID_MODEL", 0
        is_safe, clean_prompt = sanitize_prompt(prompt)
        if not is_safe:
            return "__ERROR__:TOS_REJECTED", 0

        bin_path = cls._find_bin("claude") or "claude"
        cmd = [
            bin_path,
            "-p",
            "--tools", "",
            "--safe-mode",
            "--restricted",
            "--permission-mode", "plan",
            "--permission-prompts", "none",
            "--no-session-persistence",
            "--strict-mcp-config",
            "--disable-slash-commands",
            "--setting-sources", "",
        ]
        if model and model != "default":
            cmd.extend(["--model", model])
        return cls._run_sandboxed_cli(cmd, clean_prompt, "claude_code", timeout)

    @classmethod
    def execute_codex(cls, prompt: str, model: str = "default", timeout: float = 60.0) -> Tuple[str, int]:
        """調用本機 OAuth 授權之 OpenAI Codex CLI（指定 read-only 與 ephemeral 參數 + 獨立目錄執行）。"""
        if model and not is_valid_model_name(model):
            return "__ERROR__:INVALID_MODEL", 0
        is_safe, clean_prompt = sanitize_prompt(prompt)
        if not is_safe:
            return "__ERROR__:TOS_REJECTED", 0

        bin_path = cls._find_bin("codex") or "codex"
        cmd = [
            bin_path,
            "exec",
            "--sandbox", "read-only",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
        ]
        if model and model != "default":
            cmd.extend(["-m", model])
        cmd.append("-")
        return cls._run_sandboxed_cli(cmd, clean_prompt, "codex", timeout)

    @classmethod
    def execute_gemini_cli(cls, prompt: str, model: str = "default", timeout: float = 60.0) -> Tuple[str, int]:
        """調用本機 Google OAuth 授權之 Gemini CLI（指定 sandbox 與 plan 模式 + 停用擴充 + 獨立目錄執行）。"""
        if model and not is_valid_model_name(model):
            return "__ERROR__:INVALID_MODEL", 0
        is_safe, clean_prompt = sanitize_prompt(prompt)
        if not is_safe:
            return "__ERROR__:TOS_REJECTED", 0

        bin_path = cls._find_bin("gemini") or "gemini"
        cmd = [
            bin_path,
            "--sandbox",
            "--approval-mode", "plan",
            "--allowed-mcp-server-names", "",
            "-e", "none",
            "-p", "",
        ]
        if model and model != "default":
            cmd.extend(["-m", model])
        return cls._run_sandboxed_cli(cmd, clean_prompt, "gemini_cli", timeout)


def _is_safe_endpoint_url(url: str) -> bool:
    """驗證目標伺服器 URL：遠端連線強制要求 https://，僅本機迴路 (localhost / 127.0.0.1 / ::1) 允許 http://。"""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme == "https" and bool(parsed.netloc):
            return True
        if parsed.scheme == "http" and (parsed.hostname or "").lower() in ("localhost", "127.0.0.1", "::1"):
            return True
    except Exception:
        pass
    return False


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """於轉址發送前預先攔截跨網域或降級至 HTTP 之 3xx Redirect，防止 Authorization Bearer 憑證外洩。"""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        old_parsed = urllib.parse.urlparse(req.full_url)
        new_parsed = urllib.parse.urlparse(newurl)
        if (new_parsed.scheme, new_parsed.netloc) != (old_parsed.scheme, old_parsed.netloc) or not _is_safe_endpoint_url(newurl):
            raise urllib.error.HTTPError(
                newurl,
                code,
                "Cross-origin or scheme-downgrade redirect blocked",
                headers,
                fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_SAFE_HTTP_OPENER = urllib.request.build_opener(_SafeRedirectHandler())


def _http_post(
    url: str,
    payload: Dict[str, Any],
    timeout: float = 10.0,
    token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """以 Python 內建標準庫執行 HTTP POST（強制驗證 HTTPS 或本機迴路，並在轉址發送前阻擋跨網域憑證外洩）。"""
    if not _is_safe_endpoint_url(url):
        logger.error("🚨 安全攔截：拒絕連線至非 HTTPS 之遠端不安全網址 (%s)", url)
        return None
    req_parsed = urllib.parse.urlparse(url)
    data_bytes = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "User-Agent": "berich-oauth-worker/3.1-e2ee"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-OAuth-Token"] = token
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers=headers,
        method="POST",
    )
    try:
        with _SAFE_HTTP_OPENER.open(req, timeout=timeout) as resp:
            resp_url = getattr(resp, "url", None) or (resp.geturl() if hasattr(resp, "geturl") else url)
            if isinstance(resp_url, str) and resp_url:
                resp_parsed = urllib.parse.urlparse(resp_url)
                if (resp_parsed.scheme, resp_parsed.netloc) != (req_parsed.scheme, req_parsed.netloc):
                    logger.error("🚨 安全攔截：偵測到跨網域或降級轉址 (%s -> %s)，已阻斷回應！", url, resp_url)
                    return None
            if resp.status == 200:
                body = resp.read(MAX_HTTP_RESPONSE_BYTES).decode("utf-8", errors="replace")
                return json.loads(body)
    except urllib.error.HTTPError as e:
        err_msg = str(e.reason)
        try:
            err_body = e.read(MAX_HTTP_RESPONSE_BYTES).decode("utf-8", errors="replace")
            err_json = json.loads(err_body)
            err_msg = err_json.get("detail") or err_json.get("message") or err_msg
        except Exception:
            pass
        logger.error("HTTP 錯誤 %s: %s", e.code, redact_sensitive_pii(str(err_msg)))
        if e.code in (401, 403):
            return {"status": "revoked", "error": "AUTH_FATAL", "code": e.code, "message": err_msg}
        return {"status": "error", "error": "HTTP_ERROR", "code": e.code, "message": err_msg}
    except Exception as e:
        logger.warning("連線伺服器異常 (%s): %s", url, redact_sensitive_pii(str(e)))
    return None


def run_node_worker(
    server_url: str,
    node_id: str,
    node_name: str,
    provider_type: str = "claude_code",
    supported_models: Optional[List[str]] = None,
    poll_interval: float = 2.5,
    max_cycles: Optional[int] = None,
    idle_only: bool = False,
    idle_threshold: float = 60.0,
    wallet_address: Optional[str] = None,
    oauth_token: Optional[str] = None,
    trigger_oauth_login: bool = False,
):
    """啟動跨平台 OAuth 訂閱額度共享節點常駐循環（全程強制 br_enc_v1 端對端對話內容認證加密）。"""
    server_url = server_url.rstrip("/")
    if not _is_safe_endpoint_url(server_url):
        logger.error("❌ 拒絕啟動：遠端伺服器必須使用 https:// 加密連線 (%s)", server_url)
        return
    register_url = f"{server_url}/api/compute/nodes/register"
    heartbeat_url = f"{server_url}/api/compute/nodes/heartbeat"
    claim_url = f"{server_url}/api/compute/tasks/claim"
    submit_url = f"{server_url}/api/compute/tasks/submit"

    selected_provs = [p.strip().lower() for p in (provider_type or "claude_code").split(",") if p.strip()]
    if not selected_provs:
        selected_provs = ["claude_code"]

    if trigger_oauth_login:
        for p in selected_provs:
            LocalCLIBridge.trigger_subscription_oauth_login(p)

    # 若指定了 berich 網頁核發的 OAuth Worker Token，先向後端驗證並取得綁定之會員/錢包資訊
    if oauth_token:
        verify_url = f"{server_url}/api/compute/oauth/verify_worker"
        req_nid = node_id if (node_id and not node_id.startswith("node-")) else None
        v_payload = {
            "oauth_token": oauth_token,
            "provider_type": ",".join(selected_provs),
            "os_name": platform.system(),
        }
        if req_nid:
            v_payload["node_id"] = req_nid
        v_res = _http_post(
            verify_url,
            v_payload,
            token=oauth_token,
        )
        if v_res and (v_res.get("valid_token") or v_res.get("status") in ("verified", "online", "waiting")):
            node_id = v_res.get("node_id") or node_id
            if v_res.get("wallet_address") and not wallet_address:
                wallet_address = v_res.get("wallet_address")
            logger.info("🔑 Berich OAuth 帳號授權驗證通過！已掛載訂閱: %s", ", ".join(selected_provs))
        else:
            err_msg = (v_res.get("message") if v_res else None) or "憑證驗證失敗或已被撤銷"
            logger.error("❌ 節點憑證驗證失敗: %s", err_msg)
            return

    session_secret = derive_node_session_secret(node_id, oauth_token)

    # 依多選訂閱類型自動合併候選模型清單
    if not supported_models:
        merged_models: List[str] = []
        for p in selected_provs:
            if p == "claude_code":
                merged_models.extend(["claude-opus-5-5", "claude-sonnet-5-5"])
            elif p == "codex":
                merged_models.extend(["gpt-6-astra", "gpt-6.1-sol", "gpt-5.6-terra", "gpt-6-luna"])
            elif p == "gemini_cli":
                merged_models.extend(["gemini-4-argon", "gemini-3.8-flash"])
        if not merged_models:
            merged_models = ["gemini-4-argon", "claude-sonnet-5-5", "gpt-6-astra"]
        merged_models.append("default")
        supported_models = list(dict.fromkeys(merged_models))

    anon_host = _get_anonymous_host_hash()
    system_info = {
        "os": platform.system(),
        "arch": platform.machine(),
        "host_hash": anon_host,
        "auth_mode": "oauth_subscription",
        "e2ee_protocol": "br_enc_v1",
        "selected_providers": selected_provs,
        "detected_clis": list(LocalCLIBridge.detect_available_clis().keys()),
    }

    logger.info("====================================================")
    logger.info("  💻 berich 跨平台 OAuth 訂閱額度共享節點 (macOS / Windows)")
    logger.info("  作業系統: %s (%s)", system_info["os"], system_info["arch"])
    logger.info("  節點 ID : %s", node_id)
    logger.info("  對話加密: br_enc_v1 (HKDF-SHA256 + CTR + HMAC-SHA256 全程加密)")
    logger.info("  訂閱類型: %s (支援多訂閱同時共享)", ", ".join(selected_provs))
    logger.info("  支援模型: %s", ", ".join(supported_models))
    logger.info("  閒置守護: %s (閒置門檻 %.0fs，僅啟用時生效)", "啟用" if idle_only else "全時段接單", idle_threshold)
    logger.info("====================================================")

    reg_payload = {
        "node_id": node_id,
        "node_name": node_name,
        "provider_type": selected_provs[0],
        "supported_models": supported_models,
        "oauth_token": oauth_token,
        "metadata": system_info,
    }
    reg_res = _http_post(register_url, reg_payload, token=oauth_token)
    if not reg_res:
        logger.error("無法連線至 berich 伺服器進行節點註冊: %s", server_url)
        return
    if reg_res.get("status") in ("revoked", "cheater_banned") or reg_res.get("error") == "AUTH_FATAL":
        logger.error("🚨 節點註冊失敗：授權憑證已被撤銷或拒絕存取 (%s)", reg_res.get("message") or reg_res.get("error"))
        return
    if reg_res.get("status") != "success":
        logger.error("❌ 節點註冊未成功: %s", reg_res.get("message") or reg_res.get("error") or "未知錯誤")
        return

    masked_k = reg_res.get("masked_gateway_key")
    if reg_res.get("gateway_ready") and masked_k:
        api_path = reg_res.get("api_base_path") or "/api/v1"
        api_url = f"{server_url}{api_path}"
        online_models = reg_res.get("available_models", [])
        logger.info("🎉 節點已通過自動認證上線！專屬 API Key 準備就緒: %s", masked_k)
        logger.info("📡 API Base URL: %s", api_url)
        if online_models:
            logger.info("🤖 目前可用在線模型: %s", ", ".join(online_models))
        else:
            logger.info("🤖 目前聚合池無在線模型")
    else:
        # 向後相容舊伺服器未回傳 gateway_ready 之響應，不虛假宣稱金鑰已核發或保證 VIP
        logger.info("✅ 節點連線已接受（金鑰就緒狀態無法自伺服器取得，請至網頁確認）")

    if wallet_address:
        bind_url = f"{server_url}/api/compute/nodes/bind_wallet"
        b_res = _http_post(
            bind_url,
            {"node_id": node_id, "wallet_address": wallet_address, "oauth_token": oauth_token},
            token=oauth_token,
        )
        if b_res and b_res.get("status") == "success":
            logger.info("🔗 節點已綁定 Base 錢包地址: %s", wallet_address)

    cycle_count = 0
    stop_event = threading.Event()

    def _bg_heartbeat_loop():
        while not stop_event.is_set():
            stop_event.wait(10.0)
            if stop_event.is_set():
                break
            try:
                hb_res = _http_post(
                    heartbeat_url,
                    {"node_id": node_id, "oauth_token": oauth_token},
                    timeout=5.0,
                    token=oauth_token,
                )
                if hb_res and hb_res.get("status") in ("revoked", "cheater_banned"):
                    logger.warning("節點已被伺服器註銷或撤銷，停止常駐心跳。")
                    stop_event.set()
                    break
            except Exception:
                pass

    hb_thread = threading.Thread(target=_bg_heartbeat_loop, daemon=True)
    hb_thread.start()

    logger.info("⏳ 節點已進入常駐待命狀態（每 %.1fs 輪詢，請保持此視窗開啟，隨時可按 Ctrl+C 停止）...", poll_interval)
    idle_notice_shown = False

    try:
        while True:
            if stop_event.is_set():
                logger.warning("節點憑證已失效或已被撤銷，停止常駐循環。")
                break

            cycle_count += 1
            if max_cycles and cycle_count > max_cycles:
                logger.info("已達最大測試輪數 (%d)，節點安全停止。", max_cycles)
                break

            if idle_only:
                idle_sec = get_system_idle_seconds()
                if idle_sec is None:
                    if not idle_notice_shown:
                        logger.warning("⚠️ 無法偵測本機閒置狀態，因啟用 --idle-only 安全保護機制暫停領單（節點維持在線心跳）。")
                        idle_notice_shown = True
                    time.sleep(poll_interval)
                    continue
                if idle_sec < idle_threshold:
                    if not idle_notice_shown:
                        logger.info(
                            "🛡️ 閒置守護生效中：目前偵測到滑鼠/鍵盤活動 (閒置 %.1fs < %.0fs)，待電腦閒置滿 %.0fs 後將自動接單（節點已保持在線 VIP 狀態）...",
                            idle_sec,
                            idle_threshold,
                            idle_threshold,
                        )
                        idle_notice_shown = True
                    time.sleep(poll_interval)
                    continue
                idle_notice_shown = False

            claim_res = _http_post(claim_url, {"node_id": node_id, "oauth_token": oauth_token}, token=oauth_token)
            if claim_res and claim_res.get("has_task"):
                task_id = str(claim_res.get("task_id") or "")
                raw_envelope = str(claim_res.get("encrypted_prompt") or claim_res.get("prompt") or "")
                model = (claim_res.get("model") or "default").lower()

                if not is_valid_model_name(model):
                    logger.error("🚨 安全攔截：任務 %s 模型名稱格式異常 (%r)，拒絕執行！", task_id, model)
                    _http_post(
                        submit_url,
                        {
                            "node_id": node_id,
                            "task_id": task_id,
                            "result": "",
                            "token_count": 0,
                            "error": "INVALID_MODEL",
                            "oauth_token": oauth_token,
                        },
                        token=oauth_token,
                    )
                    continue

                if not raw_envelope.startswith(ENC_ENVELOPE_PREFIX):
                    logger.error("🚨 安全攔截：任務 %s 未採用 br_enc_v1 端對端加密信封，拒絕執行明文任務！", task_id)
                    _http_post(
                        submit_url,
                        {
                            "node_id": node_id,
                            "task_id": task_id,
                            "result": "",
                            "token_count": 0,
                            "error": "E2EE_REQUIRED",
                            "oauth_token": oauth_token,
                        },
                        token=oauth_token,
                    )
                    continue

                try:
                    prompt = decrypt_conversation_payload(
                        envelope=raw_envelope,
                        secret_key=session_secret,
                        task_id=task_id,
                        node_id=node_id,
                        direction="claim",
                    )
                    raw_envelope = ""
                except ValueError as e:
                    raw_envelope = ""
                    logger.error("🚨 安全攔截：任務 %s 對話密文 HMAC 驗簽失敗 (%s)，拒絕執行！", task_id, e)
                    _http_post(
                        submit_url,
                        {
                            "node_id": node_id,
                            "task_id": task_id,
                            "result": "",
                            "token_count": 0,
                            "error": "E2EE_DECRYPT_FAILED",
                            "oauth_token": oauth_token,
                        },
                        token=oauth_token,
                    )
                    continue

                logger.info("⚡ 收到加密聚合任務: %s (模型: %s | 驗證 br_enc_v1 通過)", task_id, model)

                # 若領取任務瞬間號主操作滑鼠/鍵盤，立即退回任務 (TASK_YIELDED)
                if idle_only:
                    cur_idle = get_system_idle_seconds()
                    if cur_idle is None or cur_idle < idle_threshold:
                        prompt = ""
                        logger.info("🛑 偵測到號主操作電腦或閒置偵測失效 (cur_idle=%s)，立即退回任務 %s 交由下一位節點接手...", cur_idle, task_id)
                        _http_post(
                            submit_url,
                            {
                                "node_id": node_id,
                                "task_id": task_id,
                                "result": "",
                                "token_count": 0,
                                "error": "TASK_YIELDED:user_active",
                                "oauth_token": oauth_token,
                            },
                            token=oauth_token,
                        )
                        continue

                # 依請求模型或已勾選訂閱自動選擇對應之 OAuth CLI 執行
                target_prov = selected_provs[0]
                if "gpt" in model or "o3" in model:
                    if "codex" in selected_provs:
                        target_prov = "codex"
                elif "gemini" in model:
                    if "gemini_cli" in selected_provs:
                        target_prov = "gemini_cli"
                elif "claude" in model:
                    if "claude_code" in selected_provs:
                        target_prov = "claude_code"

                start_exec = time.time()
                if target_prov == "claude_code":
                    logger.info("  -> 調用本機 Claude Pro/Max OAuth 訂閱 (模型: %s)...", model)
                    output_text, token_count = LocalCLIBridge.execute_claude_code(prompt, model=model)
                elif target_prov == "codex":
                    logger.info("  -> 調用本機 ChatGPT Plus/Pro (Codex OAuth) 訂閱 (模型: %s)...", model)
                    output_text, token_count = LocalCLIBridge.execute_codex(prompt, model=model)
                elif target_prov == "gemini_cli":
                    logger.info("  -> 調用本機 Google Gemini OAuth 訂閱 (模型: %s)...", model)
                    output_text, token_count = LocalCLIBridge.execute_gemini_cli(prompt, model=model)
                else:
                    output_text, token_count = f"__ERROR__:AUTH_REQUIRED:{target_prov}", 0

                # 執行完畢立即抹除本機記憶體中之明文 Prompt 參照
                prompt = ""
                elapsed = time.time() - start_exec

                if output_text.startswith("__QUOTA_EXHAUSTED__") or output_text.startswith("__ERROR__:"):
                    if output_text.startswith("__ERROR__:"):
                        err_code = output_text.replace("__ERROR__:", "", 1)
                    else:
                        err_code = f"QUOTA_EXHAUSTED:{target_prov}"
                    logger.warning(
                        "🔄 偵測到本機 %s 訂閱狀態異常 (%s)，正在將任務 %s 平滑轉交給全網下一位在線節點...",
                        target_prov,
                        err_code,
                        task_id,
                    )
                    submit_payload = {
                        "node_id": node_id,
                        "task_id": task_id,
                        "result": "",
                        "token_count": 0,
                        "error": err_code,
                        "oauth_token": oauth_token,
                    }
                    _http_post(submit_url, submit_payload, token=oauth_token)
                    continue

                encrypted_result = encrypt_conversation_payload(
                    plaintext=output_text,
                    secret_key=session_secret,
                    task_id=task_id,
                    node_id=node_id,
                    direction="submit",
                )
                output_text = ""

                submit_payload = {
                    "node_id": node_id,
                    "task_id": task_id,
                    "result": encrypted_result,
                    "encrypted_result": encrypted_result,
                    "encryption": "br_enc_v1",
                    "token_count": token_count,
                    "oauth_token": oauth_token,
                }
                sub_res = _http_post(submit_url, submit_payload, token=oauth_token)
                if sub_res and sub_res.get("status") in ("revoked", "cheater_banned"):
                    logger.error("🚨 節點憑證已被伺服器撤銷，終止運行。")
                    stop_event.set()
                    break
                if sub_res and sub_res.get("status") == "success":
                    total_earned = float(sub_res.get("credits_earned", 0.0))
                    logger.info(
                        "🎉 任務 %s 加密回傳完成！耗時 %.2fs | 貢獻 %d 訂閱額度 Tokens | 累計貢獻點數: %.2f (已登入會員在線享台股 VIP 與互助額度)",
                        task_id,
                        elapsed,
                        token_count,
                        total_earned,
                    )
            else:
                if claim_res and claim_res.get("status") in ("revoked", "cheater_banned"):
                    logger.error("🚨 節點憑證已被伺服器撤銷，終止接單。")
                    stop_event.set()
                    break
                time.sleep(poll_interval)

    except KeyboardInterrupt:
        logger.info("\n使用者終止節點程式，正在退出...")
    finally:
        stop_event.set()
    logger.info("節點已安全離線。")


def main():
    detected = LocalCLIBridge.detect_available_clis()
    if detected:
        default_provider = ",".join(detected.keys())
    else:
        default_provider = "claude_code"

    anon_host = _get_anonymous_host_hash()
    parser = argparse.ArgumentParser(
        description="berich 跨平台 OAuth 訂閱額度共享程式 (支援 macOS / Windows 共享閒置 Claude / ChatGPT / Gemini 訂閱，已登入會員在線享台股盤中 VIP 與互助額度)"
    )
    parser.add_argument("--server-url", default="http://localhost:8000", help="berich 後端 API URL")
    parser.add_argument("--node-id", default=f"node-{anon_host}", help="節點唯一識別碼")
    parser.add_argument("--node-name", default=f"{platform.system()}-OAuth-{anon_host}", help="節點顯示名稱")
    parser.add_argument(
        "--provider",
        default=default_provider,
        help="OAuth 訂閱提供者，支援逗號分隔多選（如 claude_code,codex,gemini_cli）",
    )
    parser.add_argument("--oauth-token", default=None, help="從 berich.cc/compute 網頁取得的 OAuth 會員綁定憑證 (bw_oauth_...)")
    parser.add_argument("--oauth-login", action="store_true", help="啟動前自動開啟瀏覽器執行本機 AI 訂閱 CLI 之官方 OAuth 登入")
    parser.add_argument("--models", default="", help="支援的模型清單（逗號分隔）")
    parser.add_argument("--idle-only", action="store_true", help="啟用閒置避讓：僅在滑鼠鍵盤閒置時才共享訂閱額度")
    parser.add_argument("--idle-threshold", type=float, default=60.0, help="判定電腦閒置的秒數閾值（預設 60 秒）")
    parser.add_argument("--interval", type=float, default=2.0, help="輪詢間隔（秒）")
    parser.add_argument("--wallet", default=None, help="Base 鏈錢包地址 (0x...)，用於關聯節點之互助額度權益")
    parser.add_argument("--max-cycles", type=int, default=None, help="最大執行輪數（測試用途）")
    parser.add_argument("--once", action="store_true", help="僅執行單輪連線與任務檢查即結束（快速驗證用途）")
    args = parser.parse_args()

    models_list = [m.strip() for m in args.models.split(",") if m.strip()] if args.models else None
    effective_max_cycles = 1 if args.once else args.max_cycles

    run_node_worker(
        server_url=args.server_url,
        node_id=args.node_id,
        node_name=args.node_name,
        provider_type=args.provider,
        supported_models=models_list,
        poll_interval=args.interval,
        max_cycles=effective_max_cycles,
        idle_only=args.idle_only,
        idle_threshold=args.idle_threshold,
        wallet_address=args.wallet,
        oauth_token=args.oauth_token,
        trigger_oauth_login=args.oauth_login,
    )


if __name__ == "__main__":
    main()

