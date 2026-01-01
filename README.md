# BeRich OAuth Worker (`berich-oauth-worker`)

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

[![GitHub Stars](https://img.shields.io/github/stars/berich-protocol/berich-oauth-worker?style=for-the-badge&logo=github&color=fbbf24)](https://github.com/berich-protocol/berich-oauth-worker/stargazers)
[![100% Python Stdlib](https://img.shields.io/badge/Python-100%25_Stdlib_(Zero_Dependencies)-10b981?style=for-the-badge)](./prove_it_works.py)
[![macOS | Windows | Linux](https://img.shields.io/badge/Platform-macOS_%7C_Windows_%7C_Linux-3b82f6?style=for-the-badge)](./.github/workflows/verify-proof.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](./LICENSE)

> **In Plain English:**  
> Share the unused **Claude Pro/Max, ChatGPT Plus/Pro, and Google AI (Gemini)** quota you already pay \$20/month for while you're away from your computer. **While your node is online, you automatically unlock Taiwan Stock Market Intraday VIP on [BeRich (`https://berich.cc`)](https://berich.cc) plus `100,000 Tokens/day` of cross-model shared AI quota across 8 flagship models. Prefer not to run a node? Hold `$BRICH` from [Virtuals](https://app.virtuals.io/virtuals/144796) and verify ownership via a one-time Web3 wallet signature (`personal_sign`) to unlock daily AI quota and lifetime VIP!**

---

## 🔄 Two Ways to Unlock Shared AI Quota & Taiwan Stock VIP

**[BeRich (`https://berich.cc/compute`)](https://berich.cc/compute)** offers two transparent paths to access cross-model AI quota and Taiwan Stock Market Intraday VIP:

1. **💻 Path 1: Share Idle AI Subscriptions (Free Mutual Pool)**
   - Run this open-source worker when away from your keyboard to share idle Claude / ChatGPT / Gemini quota.
   - **While your node is online**: You automatically unlock **Taiwan Stock Intraday VIP** and receive **`100,000 Tokens/day` of cross-model shared AI quota** (e.g., share a single subscription and call any of the 8 models across Google, Anthropic, and OpenAI via Cursor or Cline).
2. **🔐 Path 2: Hold `$BRICH` & Verify via Web3 Wallet Signature (No Node Required)**
   - Buy and hold **`$BRICH` tokens** on **[Virtuals (`https://app.virtuals.io/virtuals/144796`)](https://app.virtuals.io/virtuals/144796)** in your own Base wallet (no staking lockup, no token transfer).
   - **Cryptographic Wallet Ownership Proof (`personal_sign` / EIP-191)**: Because on-chain holder addresses are public, simply pasting an address is rejected. You verify ownership with a one-time signature in MetaMask, Coinbase Wallet, or OKX Wallet (zero gas fees, no transaction permissions).
   - **Proportional Shared AI Quota**: Every **`1 $BRICH`** held in a signature-verified wallet unlocks **`0.5 Tokens/day`** of shared AI quota (`3,000 Tokens/day` free trial for guests; `2,000,000 $BRICH` = `1,000,000 Tokens/day`).
   - **Hold 50,000 `$BRICH`**: Unlocks **25,000 Tokens/day** of shared AI quota **PLUS Lifetime Taiwan Stock Market Intraday VIP** on `https://berich.cc` without running a node!

---

## 🤖 8 Supported Frontier Models (`/api/v1/chat/completions`)

Use your unified OpenAI-compatible API key in Cursor, Cline, or Python to call any of the 8 supported models in the shared pool:
- **Google**: `gemini-4-argon` (`Google 4 Argon`), `gemini-3.8-flash`
- **Anthropic**: `claude-opus-5-5`, `claude-sonnet-5-5`
- **OpenAI**: `gpt-6-astra`, `gpt-6.1-sol`, `gpt-5.6-terra`, `gpt-6-luna`

---

## 🛡️ Why Is It 100% Safe? (3 Simple Promises)

1. **No API Keys or Passwords Required**
   - You log in directly via official CLI tools (`claude login`, `codex login`, `gemini`) on your own computer. We never ask for or see your passwords or paid API keys.
2. **Pauses When You Use Your Computer, Works Only When You Leave**
   - Built-in mouse and keyboard detection pauses the worker within milliseconds the moment you touch your computer. Plus, it stops at 75% usage so at least 25% of your quota is always saved for you.
3. **Zero File Access & Instant Stop (`Ctrl+C`)**
   - Written purely in Python's standard library (zero `pip install` needed). It contains **zero `open()` file-reading calls** and locks CLI execution with `--tools ""`, meaning it can never touch your personal files.

---

## 🚀 Unlock Online VIP & Cross-Model AI Quota in 3 Easy Steps

### Step 1: Log in to your AI subscriptions in your terminal
- **macOS / Linux (Terminal)**:
  ```bash
  claude login && codex login && gemini
  ```
- **Windows (PowerShell)**:
  ```powershell
  claude login; codex login; gemini
  ```

### Step 2: Paste the 1-line command & click "Verify Connection"
Go to **[`https://berich.cc/compute`](https://berich.cc/compute)**:
1. Check the AI subscriptions you have.
2. Copy the launch command into your terminal, then click **"Verify Connection"** on the webpage!

### Step 3: Enjoy Intraday VIP & Cross-Model Shared AI Quota
While your node stays online, you immediately get full Taiwan Stock Intraday VIP access on `https://berich.cc` plus `100,000 Tokens/day` of mutual quota to switch between all 8 models in the shared gateway!

---

## ⚡ 3-Second Self-Check (Offline Security Proof)

Run this single command in your terminal to automatically verify all 6 safety checks in 3 seconds:

```bash
python3 prove_it_works.py
```

1. **Zero Backdoor Audit**: Scans `berich_worker.py` to prove 0 external packages and 0 `open()` file-reading calls.
2. **Idle Detection & Sandbox Check**: Confirms macOS / Windows idle pause and `--tools ""` safety lock.
3. **Multi-Subscription Support**: Verifies running Claude, ChatGPT, and Gemini together.
4. **Online VIP & Mutual Quota Settlement**: Verifies contribution tracking and online VIP / cross-model quota activation.
5. **Seamless Handover**: Confirms tasks smoothly move to another computer when you move your mouse.
6. **Account Safety & Privacy Filter**: Blocks unsafe prompts locally and masks emails, phone numbers, and keys.

---

## 💎 About `$BRICH` Token

- **Token Ticker**: `$BRICH`
- **Virtuals Official Market**: [`https://app.virtuals.io/virtuals/144796`](https://app.virtuals.io/virtuals/144796)
- **Base Contract Address**: `0x86D4854150c11b606081f8101Bf239A0c110999E`
- **Dual Utility (Verified via Web3 Wallet `personal_sign`)**:
  1. **Use Shared AI Quota**: Every `1 $BRICH` held unlocks `0.5 Tokens/day` of shared AI quota (`50,000 $BRICH` = `25,000 Tokens/day`; `2,000,000 $BRICH` = `1,000,000 Tokens/day`).
  2. **Lifetime Intraday VIP**: Hold **50,000 `$BRICH`** in your verified wallet (zero lockup, trade anytime) for lifetime intraday VIP access on `https://berich.cc`.

---

## 📂 Files in This Repo

| File | What It Does |
| :--- | :--- |
| [`berich_worker.py`](./berich_worker.py) | Main worker script: shares idle AI quota while you're away, unlocking online VIP and cross-model shared AI quota |
| [`mock_gateway_server.py`](./mock_gateway_server.py) | Local test server: lets you test multi-model routing and contribution tracking on your own machine |
| [`prove_it_works.py`](./prove_it_works.py) | 3-second safety checker: runs 6 automated security tests offline |
| [`.github/workflows/verify-proof.yml`](./.github/workflows/verify-proof.yml) | GitHub Actions CI: automatically tests every update on macOS, Windows, and Linux |
| [`LICENSE`](./LICENSE) | MIT Open Source License |

---

## ⭐ Star History

If this project helps you turn idle AI subscriptions into cross-model AI access and VIP benefits, please give us a **Star ⭐**!

[![Star History Chart](https://api.star-history.com/svg?repos=berich-protocol/berich-oauth-worker&type=Date)](https://star-history.com/#berich-protocol/berich-oauth-worker&Date)
