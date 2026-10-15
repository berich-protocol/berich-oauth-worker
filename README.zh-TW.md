# BeRich OAuth Worker (`berich-oauth-worker`)

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

[![GitHub Stars](https://img.shields.io/github/stars/berich-protocol/berich-oauth-worker?style=for-the-badge&logo=github&color=fbbf24)](https://github.com/berich-protocol/berich-oauth-worker/stargazers)
[![100% Python Stdlib](https://img.shields.io/badge/Python-100%25_內建標準庫_(免裝套件)-10b981?style=for-the-badge)](./prove_it_works.py)
[![macOS | Windows](https://img.shields.io/badge/支援系統-macOS_%7C_Windows-3b82f6?style=for-the-badge)](./.github/workflows/verify-proof.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](./LICENSE)

> **專案核心說明：**
> 把電腦上閒置的 AI 月費訂閱（Claude Pro/Max、ChatGPT Plus/Pro、Google Gemini）透過本機已登入之官方 CLI 分享給社群（無須提供 API Key），**在節點在線期間獲取 [BeRich (`https://berich.cc`)](https://berich.cc) 台股盤中 VIP 特權與跨模型互助額度**，並將社群算力匯聚為**標準 OpenAI 相容 API 網關 (`/v1/chat/completions`)**。

---

## 🔄 核心功能與兩大用途

前往 **[`https://berich.cc/compute`](https://berich.cc/compute)** 即可查看與操作系統提供的兩大頁籤：

### 1. 頁籤：「分享訂閱換 VIP」
- **分享閒置訂閱**：透過本機官方 CLI 轉發推論任務。
- **台股盤中 VIP 特權**：保持 Worker 節點在線，已登入之 BeRich 正式會員在線期間自動享有台股盤中 VIP 特權（盤中即時顯示真實選股代號與實盤部位追蹤）。
- **跨模型互助額度**：節點在線期間基礎享有每日 100,000 Tokens 跨模型互助 API 額度（驗證持幣額度若更高則取較大者）。
- **⚠️ 權益歸屬說明**：台股盤中 VIP 為實際登入會員專屬權益。請先於 BeRich 登入帳號後再取得專屬指令啟動節點以完成歸戶；若以匿名會話啟動節點，該會話可獲得共享 API 互助額度，但匿名訪客無法繼承台股看盤之會員 VIP 特權。

### 2. 頁籤：「免費用 AI（例如龍蝦 OpenClaw）」
- **標準 OpenAI 相容 API 網關**：全網節點匯聚成標準 API 網關（`https://berich.cc/api/v1`）。
- **外部客戶端調用範例**：使用者可將 Base URL 與網關 API Key 設定至支援自訂 OpenAI 端點之客戶端（例如 **OpenClaw（龍蝦）**）進行純文字對話生成。
- **⚠️ 客戶端限制聲明**：OpenClaw 僅作為相容客戶端之調用範例參考。本網關目前僅支援純文字格式，不支援 `tools` / `tool_choice`、Function Calling 工作流與多模態輸入，不代表支援完整的 OpenClaw 自動化 Agent 或工具執行。

---

## 🛠️ 前置需求與啟動方式

### 前置需求
1. **Python 環境**：需安裝 Python（CI 測試環境為 Python 3.11；Worker 主程式 100% 採用 Python 內建標準庫，無須 `pip install` 安裝任何第三方套件）。
2. **官方 AI CLI 工具**：本機需預先安裝並完成官方授權登入：
   - **Claude Pro / Max**：`claude login`
   - **ChatGPT Plus / Pro**：`codex login`
   - **Google Gemini**：`gemini`
   - 若不確定如何安裝或登入，請依各 CLI 官方現行說明操作。

### 啟動流程
1. 前往 **[`https://berich.cc/compute`](https://berich.cc/compute)** 的「**分享訂閱換 VIP**」頁籤。若需台股 VIP，請先在網站登入會員。
2. 勾選本機已具備之訂閱項目與作業系統。
3. 點擊頁面上的 **「取得本機啟動指令」** 按鈕，複製頁面產生之完整命令。
4. 將整串指令直接貼至本機終端機執行，**請勿自行修改參數或替換節點 ID**（網頁指令會自動綁定帶有憑證的 Node ID、提供者清單與可選的閒置避讓參數）。
5. **憑證與金鑰隔離**：`bw_oauth_...` 為 Worker 節點通訊憑證，與外部調用用的 API Key（`sk-berich-...`）互相獨立，切勿將任何真實憑證或金鑰公開分享。
6. **程式更新**：當 Worker 程式碼有更新時，請終止現有行程並重新取得最新啟動指令以載入新版本。

---

## 🔑 自動核發 API 金鑰與模型目錄

### 1. 自動核發與金鑰管理
- 具備簽名或登入之擁有者啟動並成功註冊真實 Worker 後，系統將自動建立或沿用專屬 API 網關金鑰（`sk-berich-...`）。
- 重複連線或重啟 Worker 會保留原金鑰與當日使用額度，不會在每次重連時自動輪替。
- 終端機與註冊回應僅顯示遮罩金鑰（如 `sk-berich-...***`）、API Base URL 與當前在線模型。完整金鑰可由已登入會員或**同一伺服器簽署 Cookie 之匿名瀏覽器會話**於 `https://berich.cc/compute` 頁面查看複製（匿名身分由伺服器簽署瀏覽器 Cookie 識別，無須強制錢包簽章）。

### 2. API 呼叫規格與端點
- **API Base URL**：`https://berich.cc/api/v1`
- **對話補全端點**：`POST https://berich.cc/api/v1/chat/completions`
- **模型目錄端點**：`GET https://berich.cc/api/v1/models`
  - 回傳目錄包含每個模型的即時在庫金鑰數 `active_pool_keys`。
  - 客戶端應篩選 `active_pool_keys > 0` 作為當前真正可用的候選模型。

### 3. 動態供應與調用限制
- **無保證固定數量或永久在線**：聚合池依賴社群節點動態在線狀態，不保證固定模型數量，亦無付費環境金鑰自動兜底。若某模型當下無在線節點承接，請求將直接被拒絕；模型出現在目錄中不代表當下百分之百可用。
- **純文字格式與工具限制**：對話訊息 `content` 必須為純文字字串；網關明確拒絕 `tools` 與 `tool_choice` 參數，不支援 `tool_calls` 與 Function Calling 工具工作流，亦不支援圖片/音訊等多模態內容。
- **SSE 串流特性**：現行 SSE 串流採用後端完整取得回答後分塊推送到客戶端之機制，非上游逐字 Token 即時串流。

---

## 📊 額度規則與 VIP 權益

### 1. 每日 API 額度計算公式
- **基礎試用額度**：一般訪客每日 3,000 Tokens。
- **在線貢獻者互助通道**：節點真實保持在線期間，額度基礎為 100,000 Tokens/日；若經驗證之持幣額度更高則取較大者：`max(100,000, 驗證後持幣額度)` Tokens/日。
- **Web3 錢包簽章與持幣額度**：
  - 需透過 Web3 錢包完成簽章驗證與餘額確認。**單純在錢包持有代幣絕不直接享有 VIP 或盤中功能！**
  - 持幣額度計算公式：`int(balance * 0.5)`。
  - 一般情況每日額度上限：`max(3,000, 持幣額度)`。
  - 若持有量達 50,000 $BRICH 以上：每日額度下限為 25,000 Tokens，即 `max(25,000, 持幣額度)`；具備有效非貢獻者 VIP 會員亦享有 25,000 額度下限。
  - **重要規則：共享在線額度與持幣額度採取「兩者取較大者 (`max`)」，而非累加！**
  - 基準試算範例（公式支援任意中間餘額，非固定階梯限制）：
    - 0 $BRICH：3,000 Tokens/日
    - 50,000 $BRICH：25,000 Tokens/日
    - 200,000 $BRICH：100,000 Tokens/日
    - 2,000,000 $BRICH：1,000,000 Tokens/日
- **額度重置時間**：台灣時間每日 08:00（UTC 00:00）。
- **離線狀態處理**：節點離線或憑證撤銷時，立即失去在線共享資格，額度回退至持幣驗證或基礎額度；不累積離線 VIP 天數。

### 2. 台股盤中 VIP 權益對照表
在線期間已登入會員自動開通台股盤中 VIP：

| 項目 | 一般訪客 | VIP 會員 |
| :--- | :--- | :--- |
| 盤中 AI 選股 | 盤中隱藏代號，15:00 收盤後公開 | 盤中即時顯示真實股票代號 |
| 實盤部位追蹤 | 盤中隱藏代號，15:00 收盤後公開 | 盤中同步查看建倉與停利停損 |

### 3. 節點貢獻點數與激勵
- 節點註冊或唯讀驗證不會產生即時獎勵。
- 終端顯示之貢獻點數依據實際成功承接並完成之推論任務結算，不承諾保證鏈上提領、鑄造或投資收益。
- 代幣合約地址（Base 鏈）：`0x86D4854150c11b606081f8101Bf239A0c110999E`（僅供技術整合識別，不構成任何財務或投資建議）。

---

## 🛡️ 運作機制、限制與風險揭露

1. **本機 CLI 調用與授權傳輸**：Worker 透過本機已登入之官方 CLI 轉發推論。官方 CLI 運行時仍會讀取其本機登入憑證與設定，請求會經過調度服務與官方上游伺服器。程式透過指定空白暫存目錄與停用工具參數降低風險，但**不等於完整系統沙盒隔離，亦不保證無本機檔案讀取**。
2. **前置閒置檢查機制 (Idle Guard)**：閒置避讓為選用參數（網頁指令預設帶入 `--idle-only`，預設閾值為 60 秒 `--idle-threshold 60.0`）。啟用時，Worker 於任務領取前與呼叫 CLI 前雙重檢查系統閒置狀態；偵測失敗或使用者活躍時停止領單。**若 CLI 已在執行中，移動滑鼠或鍵盤不會即時強制殺死進行中的 CLI 行程**；待當前任務完成後，若偵測到使用者正在操作電腦，才會暫停領取新任務。若未加上 `--idle-only`，Worker 將處於全時段接單狀態。
3. **跨平台閒置偵測差異**：macOS 與 Windows 支援原生閒置讀取；Linux 系統目前閒置偵測回傳 `None`，若於 Linux 啟用 `--idle-only` 將因安全保護機制而無法領單，**Linux 不支援完整閒置避讓模式**。
4. **服務端用量推估機制**：服務端後端維持 5 小時滾動用量推估，用於社群池容量調度並設有 75% 軟上限保護，非本機 Worker 直接追蹤官方額度。此數值為服務端推估，無法查詢官方後端真實剩餘額度，亦不保證保留 25% 官方額度。
5. **關鍵字過濾與脫敏局限**：內建關鍵字過濾與正規表達式脫敏僅為輔助過濾手段，無法保證絕對安全、不保證完全去識別化。
6. **服務條款與無封號保證 (No Ban Guarantee)**：本專案為開源分散式運算技術實作，無法保證零封號風險。各 AI 供應商隨時可能更新服務條款，使用者須自行評估並承擔使用帳號之相關風險。

---

## 🧪 離線模擬檢查 (Offline Simulation Check)

您可在本機終端機執行模擬檢查腳本，檢驗程式碼設定與離線轉發邏輯：

```bash
python3 prove_it_works.py
```

> **重要說明**：此腳本為純本機離線 mock 測試與靜態設定檢查（不連外網、不打真實上游），僅用於驗證受測範例配置，**不能證明零後門，亦不等於真實 CLI、Windows/官方相容性或安全認證**。
- **AST 靜態語法檢查**：檢查 `berich_worker.py` 標準庫引用與語法結構。
- **前置閒置與參數檢查**：檢查系統閒置時間讀取邏輯與 CLI 參數組裝。
- **多訂閱掛載模擬**：於本地 mock 伺服器驗證多供應商資料結構。
- **任務派發與完單模擬**：模擬端點派單與首筆完單狀態更新。
- **額度耗盡轉派模擬**：測試 429 錯誤分類與任務重回隊列邏輯。
- **文字與脫敏規則測試**：測試內建安全過濾字詞與 regex 遮蔽效果。

---

## 📂 檔案清單

| 檔案 | 實際用途 |
| :--- | :--- |
| [`berich_worker.py`](./berich_worker.py) | 主程式：在電腦閒置時轉發 AI 任務，在線期間享有 BeRich 台股盤中 VIP |
| [`mock_gateway_server.py`](./mock_gateway_server.py) | 本機測試伺服器：在本地環境模擬測試 API 轉發與任務回報 |
| [`prove_it_works.py`](./prove_it_works.py) | 離線模擬檢查腳本：在本地驗證受測範例、參數配置與離線轉發邏輯 |
| [`.github/workflows/verify-proof.yml`](./.github/workflows/verify-proof.yml) | GitHub CI：於虛擬機器執行離線模擬檢查 |
| [`LICENSE`](./LICENSE) | MIT 開源授權條款 |

---

## ⭐ Star History

如果這個專案能幫你把閒置的 AI 訂閱額度轉化為實質價值，歡迎點右上角 **Star ⭐** 支持我們！

[![Star History Chart](https://api.star-history.com/svg?repos=berich-protocol/berich-oauth-worker&type=Date)](https://star-history.com/#berich-protocol/berich-oauth-worker&Date)
