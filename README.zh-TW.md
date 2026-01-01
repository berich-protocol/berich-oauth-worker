# BeRich OAuth Worker (`berich-oauth-worker`)

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

[![GitHub Stars](https://img.shields.io/github/stars/berich-protocol/berich-oauth-worker?style=for-the-badge&logo=github&color=fbbf24)](https://github.com/berich-protocol/berich-oauth-worker/stargazers)
[![100% Python Stdlib](https://img.shields.io/badge/Python-100%25_內建標準庫_(免裝套件)-10b981?style=for-the-badge)](./prove_it_works.py)
[![macOS | Windows | Linux](https://img.shields.io/badge/支援系統-macOS_%7C_Windows_%7C_Linux-3b82f6?style=for-the-badge)](./.github/workflows/verify-proof.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](./LICENSE)

> **一句話看懂這個專案：**  
> 把你每個月花 \$20 美金訂閱、但睡覺或離開電腦時根本用不完的 **Claude Pro/Max、ChatGPT Plus/Pro、Google AI (Gemini)** 閒置額度分享給社群，**在線期間自動免費享 [BeRich (`https://berich.cc`)](https://berich.cc) 全站台股盤中 VIP，並獲得每日 `100,000 Tokens` 跨模型共享 AI 互助額度（可自由切換呼叫池內 8 大頂尖模型）；不想開機跑節點的人，則可於 [Virtuals 市場](https://app.virtuals.io/virtuals/144796) 持有 `$BRICH` 並透過 Web3 錢包簽章驗證，免開機永久解鎖台股 VIP 與每日共享 AI 額度！**

---

## 🔄 雙軌生態架構：去中心化算力網 (DePIN) 驅動台股 AI 智慧體 (Agent)

本專案同時作為 **[BeRich (`https://berich.cc`)](https://berich.cc)** 全台股 AI 投資智慧體的去中心化推論算力網絡，並為全球開發者提供 **「以 1 換 8」** 的跨模型訂閱互助交換通道：

1. **💻 方式一：分享閒置 AI 訂閱（免費互助通道）**
   - 離開電腦時執行本開源節點，分享閒置的 Claude / ChatGPT / Gemini 訂閱額度。
   - **節點保持在線期間**：自動免費開通 **BeRich 全站台股盤中 VIP**，並享每日 **`100,000 Tokens` 跨模型共享 AI 互助額度**（例如你只有訂 Claude，分享後在 Cursor / Cline 也能免費切換呼叫池內的 Google 4 Argon、GPT-6 Astra 等全系列模型）。
2. **🔐 方式二：錢包持有 `$BRICH` 並完成簽章驗證（免開機通道）**
   - 直接於 **[Virtuals 官方市場 (`https://app.virtuals.io/virtuals/144796`)](https://app.virtuals.io/virtuals/144796)** 買入 **`$BRICH` 代幣**放在自己的 Base 鏈錢包（免質押鎖倉、免轉帳）。
   - **Web3 錢包簽章驗證**：透過 MetaMask / Coinbase Wallet / OKX Wallet 完成一次性簽章確認錢包所有權（免 Gas 費、免轉帳授權）。
   - **按持幣量解鎖共享 AI 額度**：已簽章驗證之錢包每持有 **`1 顆 $BRICH`** 即解鎖每日 **`0.5 Tokens`** 的共享 AI 額度（未持幣每日試用 3,000 Tokens；持滿 200 萬顆享每日 100 萬 Tokens）。
   - **持滿 50,000 顆 `$BRICH`（5 萬顆）**：每日享 **25,000 Tokens** 共享 AI 額度，**同時免開機永久解鎖 `https://berich.cc` 全站台股盤中 VIP**！

---

## 🤖 支援跨模型互助呼叫之 8 大頂尖模型 (`/api/v1/chat/completions`)

透過共享池聚合網關（相容 OpenAI SDK、Cursor、Cline），可一鍵切換呼叫三大廠牌共 8 款主力模型：
- **Google**：`gemini-4-argon` (`Google 4 Argon`)、`gemini-3.8-flash`
- **Anthropic**：`claude-opus-5-5`、`claude-sonnet-5-5`
- **OpenAI**：`gpt-6-astra`、`gpt-6.1-sol`、`gpt-5.6-terra`、`gpt-6-luna`

---

## 🛡️ 為什麼 100% 安全？（三大白話保證）

1. **不用交出 API Key，不碰你的帳號密碼**
   - 你只要在自己電腦終端機打 `claude login`、`codex login` 或 `gemini` 完成官方登入即可，我們不收、也看不到你的帳密與付費金鑰。
2. **你在用電腦時它就休息，你離開電腦它才工作**
   - 內建滑鼠與鍵盤偵測：只要你一動滑鼠或打字，程式在幾毫秒內立刻暫停禮讓給你；而且最多只會用掉 75% 額度，永遠保留 25% 以上給你自己用。
3. **不讀你電腦裡任何檔案，隨時 `Ctrl+C` 就關掉**
   - 整支程式只用 Python 內建標準庫（免裝任何套件），裡面**連一個 `open()` 讀檔指令都沒有**，並強制加上 `--tools ""` 關閉所有工具權限，絕對碰不到你的個人檔案。

---

## 🚀 30 秒極簡三步驟開通在線 VIP 與跨模型互助額度

### 第 1 步：在終端機登入你有的 AI 會員（有訂哪個就跑哪一行，不用全跑）
- **有訂 Claude Pro / Max**：`claude login`
- **有訂 ChatGPT Plus / Pro**：`codex login`
- **有訂 Google AI (Gemini)**：`gemini`

### 第 2 步：貼上一行啟動指令並點擊「驗證連線」
前往 **[`https://berich.cc/compute`](https://berich.cc/compute)**：
1. 勾選你有的 AI 會員（可複選）。
2. 複製頁面上的啟動指令貼到終端機執行，再點一下頁面上的 **「我已執行指令，驗證連線」**。

### 第 3 步：立即使用台股盤中 VIP 與跨模型共享 AI 額度
只要節點保持在線，即可立即在 `berich.cc` 查看盤中即時選股與實盤部位，並於第 2 個頁籤領取專屬聚合 API Key，在 Cursor / Cline 或自己的程式中使用每日 `100,000 Tokens` 互助額度切換呼叫池內 8 大模型！

---

## ⚡ 3 秒鐘自己驗證安全性（免連網自動檢查）

打開終端機直接跑這行指令，3 秒鐘自動檢查完 6 項安全鐵證：

```bash
python3 prove_it_works.py
```

1. **程式碼零後門檢查**：自動掃描 `berich_worker.py`，證明 0 外部套件、0 `open()` 讀檔指令。
2. **雙平台與沙盒檢查**：確認 macOS / Windows 滑鼠動就暫停，且強制開啟 `--tools ""` 安全限制。
3. **多帳號同時掛載**：實測同時掛載 Claude、ChatGPT、Gemini 三大訂閱。
4. **在線 VIP 與互助額度結算**：實測完成跨模型 AI 分析任務後，自動記錄共享貢獻並啟用在線 VIP 與互助額度。
5. **跨節點自動接力**：當你動滑鼠暫停或額度用完時，任務自動交棒給下一台電腦，不中斷對話。
6. **防封號與個資保護**：自動攔截違規問題，並自動把信箱、電話、金鑰打碼隱藏。

---

## 💎 關於 `$BRICH` 代幣資訊

- **代幣代號 (Ticker)**：`$BRICH`
- **Virtuals 官方交易市場**：[`https://app.virtuals.io/virtuals/144796`](https://app.virtuals.io/virtuals/144796)
- **Base 鏈合約地址**：`0x86D4854150c11b606081f8101Bf239A0c110999E`
- **代幣雙重賦能（需完成 Web3 錢包 `personal_sign` 簽章驗證）**：
  1. **共享 AI 額度**：每持有 `1 顆 $BRICH` 解鎖每日 `0.5 Tokens` 共享 AI 額度（5 萬顆享每日 25,000 Tokens；200 萬顆享每日 100 萬 Tokens）。
  2. **解鎖台股盤中 VIP**：錢包持滿 **50,000 顆 `$BRICH`**（免鎖倉，隨時可買賣）即可免開機永久解鎖 `https://berich.cc` 全站台股盤中 VIP。

---

## 📂 檔案說明

| 檔案 | 白話用途 |
| :--- | :--- |
| [`berich_worker.py`](./berich_worker.py) | 主程式：在你離開電腦時分享閒置 AI 額度，在線自動享台股 VIP 與跨模型共享 AI 互助額度 |
| [`mock_gateway_server.py`](./mock_gateway_server.py) | 本機測試伺服器：讓你在自己電腦上模擬測試跨模型 API 轉發與互助貢獻結算 |
| [`prove_it_works.py`](./prove_it_works.py) | 3 秒安全驗證腳本：不用連外網，自動幫你檢查程式碼有沒有後門 |
| [`.github/workflows/verify-proof.yml`](./.github/workflows/verify-proof.yml) | GitHub 自動測試：每次更新自動在 Mac / Windows / Linux 跑安全檢查 |
| [`LICENSE`](./LICENSE) | MIT 開源授權條款 |

---

## ⭐ Star History（累積星星數趨勢圖）

如果這個專案能幫你把閒置的 AI 訂閱額度變成跨模型互助額度與台股 VIP 權益，歡迎點右上角 **Star ⭐** 支持我們！

[![Star History Chart](https://api.star-history.com/svg?repos=berich-protocol/berich-oauth-worker&type=Date)](https://star-history.com/#berich-protocol/berich-oauth-worker&Date)
