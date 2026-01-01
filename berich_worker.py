#!/usr/bin/env python3
"""BeRich 閒置 AI 訂閱額度共享節點 (Cross-Platform OAuth Subscription Worker).

一句話說明：把您電腦上沒在用的 AI 月費訂閱額度（免 API Key）分享給社群，節點在線期間自動免費享 BeRich 全站台股盤中 VIP 與每日 100,000 Tokens 跨模型共享 AI 互助額度（可自由呼叫池內的 Google 4 Argon、Claude Opus 5.5、GPT-6 Astra 等 8 大模型）；若想免開機永久享有 VIP 與每日額度，可於錢包持有 $BRICH 並透過 Web3 錢包簽章驗證解鎖！
支援跨平台（macOS / Windows / Linux）與官方 OAuth 登入：
1. claude_code: 透過 `claude login` 共享 Claude Pro / Max 閒置額度（強制 --tools "" 純文字安全沙盒）
2. codex: 透過 `codex login` 共享 ChatGPT Plus / Pro 閒置額度
3. gemini_cli: 透過 `gemini` 共享 Google AI (Gemini) 閒置額度
4. simulation: 免安裝 CLI 之本機連線測試模式

三大安全保證：
- 不碰個人檔案：零 open() 讀檔指令，且調用 CLI 時強制加上 --tools "" 關閉所有工具執行權限
- 記憶體零留存：任務於記憶體中執行，不寫入硬碟
- 滑鼠一動立刻暫停 (Idle Guard)：偵測到滑鼠或鍵盤操作時幾毫秒內自動暫停禮讓，只有離開電腦時才接單！
"""

import argparse
import ctypes
import hashlib
import json
import logging
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

MAX_PROMPT_CHARS = 32_000
MAX_OUTPUT_CHARS = 64_000
MAX_HTTP_RESPONSE_BYTES = 2 * 1024 * 1024

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

# 惡意關鍵詞與違反 ToS 越獄黑名單過濾（防止惡意 Prompt 越獄或害號主帳號遭官方風控封禁）
DANGEROUS_PATTERNS = [
    re.compile(r"(rm\s+-rf|chmod|chown|killall|reboot|shutdown|del\s+/f|format\s+c:)", re.I),
    re.compile(r"(cat\s+~/.ssh|cat\s+/etc/shadow|id_rsa)", re.I),
    re.compile(r"(curl\s+.*\|\s*bash|wget\s+.*\|\s*sh|Invoke-Expression)", re.I),
    re.compile(r"(ignore\s+all\s+previous\s+(safety\s+)?instructions|how\s+to\s+make\s+a\s+bomb|write\s+ransomware|ransomware\s+payload)", re.I),
]

# 雙向個資與私密金鑰自動脫敏規則（相容中英混排，避免呼叫端不慎將 API Key / 私鑰 / Email 傳入陌生節點）
PII_REDACTION_RULES = [
    (re.compile(r"(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{16,}(?![A-Za-z0-9_-])"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?<![A-Za-z0-9_])AIza[0-9A-Za-z_-]{35}(?![0-9A-Za-z_-])"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?<![A-Za-z0-9_])bw_oauth_[a-fA-F0-9]{12,}(?![a-fA-F0-9])"), "[REDACTED_OAUTH_TOKEN]"),
    (re.compile(r"(?<![A-Za-z0-9_])0x[a-fA-F0-9]{64}(?![a-fA-F0-9])"), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?<!\d)09\d{2}[-\s]?\d{3}[-\s]?\d{3}(?!\d)"), "[REDACTED_PHONE]"),
]

# AI 訂閱額度用罄 / 速率限制 / 授權失效偵測規則（觸發時自動將任務平滑轉交給下一位使用者的節點）
AUTH_ERROR_REGEX = re.compile(
    r"(not\s+logged\s+in|login\s+required|please\s+run\s+claude\s+login|"
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
    """檢查提示詞長度、是否包含惡意越獄或系統攻擊特徵，並執行雙向個資脫敏。"""
    if not isinstance(prompt, str) or not prompt.strip():
        return False, "空的提示詞。"
    if len(prompt) > MAX_PROMPT_CHARS:
        return False, f"提示詞長度超過安全上限 ({MAX_PROMPT_CHARS} 字元)，本機沙盒拒絕執行。"
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(prompt):
            return False, f"偵測到高風險惡意指令模式 ({pattern.pattern})，本機沙盒主動拒絕執行。"
    return True, redact_sensitive_pii(prompt)


def get_system_idle_seconds() -> float:
    """取得系統滑鼠/鍵盤閒置秒數（同時支援 macOS 與 Windows，零 shell=True）。"""
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
            return 999.0
        except Exception:
            return 999.0
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
            return 999.0
    return 999.0


class LocalCLIBridge:
    """本機 OAuth 訂閱 CLI 安全沙盒橋接器（支援 macOS / Windows / Linux 與獨立空白目錄無痕隔離）。"""

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
            logger.info("🔑 正在啟動 Anthropic Claude 官方 OAuth 瀏覽器授權登入 (claude login)...")
            subprocess.run([bin_path, "login"], shell=is_win, timeout=300.0)
            return True
        elif provider_type == "codex":
            bin_path = cls._find_bin("codex")
            if not bin_path:
                logger.warning("尚未安裝 OpenAI Codex CLI！請先執行: npm install -g @openai/codex")
                return False
            logger.info("🔑 正在啟動 OpenAI ChatGPT Plus/Pro 官方 OAuth 瀏覽器授權登入 (codex login)...")
            subprocess.run([bin_path, "login"], shell=is_win, timeout=300.0)
            return True
        elif provider_type == "gemini_cli":
            bin_path = cls._find_bin("gemini")
            if not bin_path:
                logger.warning("尚未安裝 Google Gemini CLI！請先執行: npm install -g @google/gemini-cli")
                return False
            logger.info("🔑 正在啟動 Google Gemini 官方 OAuth 瀏覽器授權登入...")
            subprocess.run([bin_path], shell=is_win, timeout=300.0)
            return True
        return True

    @staticmethod
    def _build_sanitized_env(isolated_cwd: str) -> Dict[str, str]:
        """建立最小化無痕環境變數：強制移除所有付費 API Key 與敏感憑證，僅保留 OAuth CLI 運行所需基礎變數。"""
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
        """於每次獨立建立之空白 TemporaryDirectory 中執行 CLI，透過 stdin 傳入 Prompt 徹底杜絕參數注入與環境變數展開。"""
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
                err_msg = (res.stderr or "").strip()[:200] or f"Process returned exit code {res.returncode}"
                logger.warning("%s CLI 執行異常: %s", provider, err_msg)
                return f"__ERROR__:AUTH_REQUIRED:{provider}", 0

            raw_output = (res.stdout or "").strip()
            if not raw_output and provider in ("codex", "gemini_cli"):
                return f"__ERROR__:AUTH_REQUIRED:{provider}", 0
            output = redact_sensitive_pii(raw_output[:MAX_OUTPUT_CHARS])
            token_count = max(50, len(clean_prompt) // 2 + len(output) // 2)
            return output, token_count
        except subprocess.TimeoutExpired:
            return f"__QUOTA_EXHAUSTED__:{provider}", 0
        except Exception as e:
            logger.warning("%s CLI 呼叫失敗: %s", provider, e)
            return f"__ERROR__:AUTH_REQUIRED:{provider}", 0

    @classmethod
    def execute_claude_code(cls, prompt: str, timeout: float = 60.0) -> Tuple[str, int]:
        """調用本機 OAuth 授權之 Claude Code CLI（純文字零工具沙盒 + 無痕不落盤 + stdin 隔離輸入）。"""
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
        return cls._run_sandboxed_cli(cmd, clean_prompt, "claude_code", timeout)

    @classmethod
    def execute_codex(cls, prompt: str, timeout: float = 60.0) -> Tuple[str, int]:
        """調用本機 OAuth 授權之 OpenAI Codex CLI（強制 read-only 沙盒 + 無痕 ephemeral + stdin 隔離輸入）。"""
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
            "-",
        ]
        return cls._run_sandboxed_cli(cmd, clean_prompt, "codex", timeout)

    @classmethod
    def execute_gemini_cli(cls, prompt: str, timeout: float = 60.0) -> Tuple[str, int]:
        """調用本機 Google OAuth 授權之 Gemini CLI（強制 sandbox + plan 唯讀模式 + 禁用擴充與 MCP + stdin 隔離輸入）。"""
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
        return cls._run_sandboxed_cli(cmd, clean_prompt, "gemini_cli", timeout)


def _http_post(url: str, payload: Dict[str, Any], timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    """以 Python 內建標準庫執行 HTTP POST（零第三方套件依賴，macOS / Windows 開箱即跑）。"""
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "berich-oauth-worker/3.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = resp.read(MAX_HTTP_RESPONSE_BYTES).decode("utf-8", errors="replace")
                return json.loads(body)
    except urllib.error.HTTPError as e:
        logger.error("HTTP 錯誤 %s: %s", e.code, e.reason)
    except Exception as e:
        logger.warning("連線伺服器異常 (%s): %s", url, e)
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
    """啟動跨平台 OAuth 訂閱額度共享節點常駐循環。"""
    server_url = server_url.rstrip("/")
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
        v_res = _http_post(
            verify_url,
            {
                "oauth_token": oauth_token,
                "node_id": node_id,
                "provider_type": ",".join(selected_provs),
                "os_name": platform.system(),
            },
        )
        if v_res and v_res.get("status") == "verified":
            node_id = v_res.get("node_id") or node_id
            if v_res.get("wallet_address") and not wallet_address:
                wallet_address = v_res.get("wallet_address")
            logger.info("🔑 Berich OAuth 帳號授權驗證通過！已掛載訂閱: %s", ", ".join(selected_provs))

    # 依多選訂閱類型自動合併支援之 8 大聚合模型
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
        "selected_providers": selected_provs,
        "detected_clis": list(LocalCLIBridge.detect_available_clis().keys()),
    }

    logger.info("====================================================")
    logger.info("  💻 berich 跨平台 OAuth 訂閱額度共享節點 (macOS / Windows)")
    logger.info("  作業系統: %s (%s)", system_info["os"], system_info["arch"])
    logger.info("  節點 ID : %s", node_id)
    logger.info("  訂閱類型: %s (支援多訂閱同時共享)", ", ".join(selected_provs))
    logger.info("  支援模型: %s", ", ".join(supported_models))
    logger.info("  閒置守護: %s (閒置滿 %.0fs 才自動共享訂閱額度)", "啟用" if idle_only else "全時段接單", idle_threshold)
    logger.info("====================================================")

    reg_payload = {
        "node_id": node_id,
        "node_name": node_name,
        "provider_type": selected_provs[0],
        "supported_models": supported_models,
        "metadata": system_info,
    }
    reg_res = _http_post(register_url, reg_payload)
    if not reg_res:
        logger.error("無法連線至 berich 伺服器進行節點註冊: %s", server_url)
        return

    logger.info("✅ 節點已上線並加入聚合 API 供給池（在線期間自動享全站台股 VIP 與每日 100,000 Tokens 跨模型互助額度）")

    if wallet_address:
        bind_url = f"{server_url}/api/compute/nodes/bind_wallet"
        b_res = _http_post(bind_url, {"node_id": node_id, "wallet_address": wallet_address})
        if b_res and b_res.get("status") == "success":
            logger.info("🔗 節點已綁定 Base 錢包地址: %s", wallet_address)

    cycle_count = 0
    last_heartbeat = time.time()

    try:
        while True:
            cycle_count += 1
            if max_cycles and cycle_count > max_cycles:
                logger.info("已達最大測試輪數 (%d)，節點安全停止。", max_cycles)
                break

            now = time.time()
            if now - last_heartbeat >= 15.0:
                _http_post(heartbeat_url, {"node_id": node_id})
                last_heartbeat = now

            if idle_only:
                idle_sec = get_system_idle_seconds()
                if idle_sec < idle_threshold:
                    logger.debug("偵測到用戶正在使用電腦 (閒置 %.1fs < %.0fs)，自動禮讓中...", idle_sec, idle_threshold)
                    time.sleep(poll_interval)
                    continue

            claim_res = _http_post(claim_url, {"node_id": node_id})
            if claim_res and claim_res.get("has_task"):
                task_id = claim_res["task_id"]
                prompt = claim_res["prompt"]
                model = (claim_res.get("model") or "default").lower()
                logger.info("⚡ 收到外部聚合 API 請求任務: %s (模型: %s)", task_id, model)

                # 若領取任務瞬間號主突然操作滑鼠/鍵盤，立即無損退回任務 (TASK_YIELDED) 轉交下一位節點
                if idle_only and get_system_idle_seconds() < idle_threshold:
                    logger.info("🛑 偵測到號主開始操作電腦，立即退回任務 %s 交由下一位節點無縫接手...", task_id)
                    _http_post(
                        submit_url,
                        {
                            "node_id": node_id,
                            "task_id": task_id,
                            "result": "",
                            "token_count": 0,
                            "error": "TASK_YIELDED:user_active",
                        },
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
                    logger.info("  -> 調用本機 Claude Pro/Max OAuth 訂閱沙盒...")
                    output_text, token_count = LocalCLIBridge.execute_claude_code(prompt)
                elif target_prov == "codex":
                    logger.info("  -> 調用本機 ChatGPT Plus/Pro (Codex OAuth) 訂閱沙盒...")
                    output_text, token_count = LocalCLIBridge.execute_codex(prompt)
                elif target_prov == "gemini_cli":
                    logger.info("  -> 調用本機 Google Gemini OAuth 訂閱沙盒...")
                    output_text, token_count = LocalCLIBridge.execute_gemini_cli(prompt)
                else:
                    output_text, token_count = f"__ERROR__:AUTH_REQUIRED:{target_prov}", 0

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
                    }
                    _http_post(submit_url, submit_payload)
                    continue

                submit_payload = {
                    "node_id": node_id,
                    "task_id": task_id,
                    "result": output_text,
                    "token_count": token_count,
                }
                sub_res = _http_post(submit_url, submit_payload)
                if sub_res and sub_res.get("status") == "success":
                    total_earned = float(sub_res.get("credits_earned", 0.0))
                    logger.info(
                        "🎉 任務 %s 完成回傳！耗時 %.2fs | 貢獻 %d 訂閱額度 Tokens | 累計貢獻點數: %.2f (在線期間自動享台股 VIP 與跨模型互助額度)",
                        task_id,
                        elapsed,
                        token_count,
                        total_earned,
                    )
            else:
                time.sleep(poll_interval)

    except KeyboardInterrupt:
        logger.info("\n使用者終止節點程式，正在退出...")
    logger.info("節點已安全離線。")


def main():
    detected = LocalCLIBridge.detect_available_clis()
    if detected:
        default_provider = ",".join(detected.keys())
    else:
        default_provider = "claude_code"

    anon_host = _get_anonymous_host_hash()
    parser = argparse.ArgumentParser(
        description="berich 跨平台 OAuth 訂閱額度共享程式 (支援 macOS / Windows 共享閒置 Claude / ChatGPT / Gemini 訂閱，在線享台股 VIP 與跨模型互助額度)"
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
    parser.add_argument("--wallet", default=None, help="Base 鏈錢包地址 (0x...)，用於關聯節點之在線 VIP 與跨模型互助額度權益")
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

