# BeRich OAuth Worker (`berich-oauth-worker`)

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

[![GitHub Stars](https://img.shields.io/github/stars/berich-protocol/berich-oauth-worker?style=for-the-badge&logo=github&color=fbbf24)](https://github.com/berich-protocol/berich-oauth-worker/stargazers)
[![100% Python Stdlib](https://img.shields.io/badge/Python-100%25_Stdlib_(Zero_Dependencies)-10b981?style=for-the-badge)](./prove_it_works.py)
[![macOS | Windows](https://img.shields.io/badge/Platform-macOS_%7C_Windows-3b82f6?style=for-the-badge)](./.github/workflows/verify-proof.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](./LICENSE)

> **In Plain English:**
> Share the unused quota of your active AI subscriptions (Claude Pro/Max, ChatGPT Plus/Pro, Google Gemini) via your locally authenticated official CLIs without sharing API keys. **Earn [BeRich (`https://berich.cc`)](https://berich.cc) Taiwan Stock Market Intraday VIP access and cross-model mutual compute quota while your node is online**, while pooling compute into a **standard OpenAI-compatible API gateway (`/v1/chat/completions`)**.

---

## 🔄 Core Features & Two Primary Use Cases

Visit **[`https://berich.cc/compute`](https://berich.cc/compute)** to explore the two primary workflow tabs:

### 1. Tab: "Share Subscriptions for VIP" (`分享訂閱換 VIP`)
- **Share Idle Subscriptions**: Relay inference tasks through local official CLIs when your computer is idle.
- **Taiwan Stock Intraday VIP**: Keeping the worker online grants authenticated BeRich member accounts real-time Taiwan Stock VIP privileges (real-time stock ticker reveals for intraday AI picks and live portfolio tracking).
- **Cross-Model Mutual Quota**: Active online contributors receive a base quota of 100,000 Tokens/day (higher if verified holding quota exceeds this floor).
- **⚠️ Account Attribution Notice**: Taiwan Stock VIP is an authenticated member privilege. Please sign in to your BeRich account before generating your startup command to bind VIP privileges. If launched in an anonymous session, you receive API gateway quota, but anonymous sessions cannot inherit website stock market VIP privileges.

### 2. Tab: "Free AI Usage (e.g. OpenClaw)" (`免費用 AI（例如龍蝦 OpenClaw）`)
- **OpenAI-Compatible API Gateway**: Community nodes aggregate compute into a standard gateway (`https://berich.cc/api/v1`).
- **External Client Example**: Connect clients supporting custom OpenAI endpoints (such as **OpenClaw**) to perform pure text chat generation.
- **⚠️ Client Scope Notice**: OpenClaw is cited strictly as a client connection example. This gateway only supports text format; `tools` and `tool_choice` are rejected, function calling / `tool_calls` workflows are unsupported, and multimodal inputs are rejected. It does not imply support for full automated agent workflows.

---

## 🛠️ Prerequisites & Getting Started

### Prerequisites
1. **Python Environment**: Python installed is required (tested on Python 3.11; the worker relies 100% on the Python standard library with zero `pip install` requirements).
2. **Official AI CLIs**: Pre-install and authenticate the relevant official CLI tools locally:
   - **Claude Pro / Max**: `claude auth login`
   - **ChatGPT Plus / Pro**: `codex login`
   - **Google Gemini**: `gemini` (select Sign in with Google after launch)
   - If unsure of installation steps, consult each CLI tool's official documentation.

### Startup Steps
1. Navigate to the "**分享訂閱換 VIP**" tab at **[`https://berich.cc/compute`](https://berich.cc/compute)**. Log in first if you wish to unlock Taiwan Stock VIP.
2. Select your active subscriptions and operating system.
3. Click the button **「取得本機啟動指令」** (Get Local Launch Command) on the page to copy the complete generated command.
4. Paste and execute the entire command unchanged in your terminal; **do not manually modify parameters or substitute node IDs** (the web command automatically bundles your authorized Node ID, provider arguments, and optional idle flag).
5. **Token & Key Isolation**: The `bw_oauth_...` token authorizes worker node communication and is completely separate from the API gateway key (`sk-berich-...`) used for chat completions. Never publicly share your worker command or private keys.
6. **Worker Updates**: When updating worker code, terminate the running process and obtain an updated launch command to reload the latest version.

---

## 🔑 Automatic API Key & Model Catalogue

### 1. Automatic Key Issuance & Retention
- When an authenticated or signed owner registers an active worker, the server automatically issues or reuses a dedicated API gateway key (`sk-berich-...`).
- Reconnecting or restarting the worker preserves the same key and accumulated daily usage; keys do not rotate on reconnect.
- The terminal and register response display a masked key only (e.g., `sk-berich-...***`), API Base URL, and online model IDs. The full key can be retrieved from `https://berich.cc/compute` by the authenticated account or within the **same server-signed browser session** (anonymous identity is managed via server-signed browser cookie without requiring a wallet signature).

### 2. API Endpoints & Specifications
- **Base URL**: `https://berich.cc/api/v1`
- **Chat Endpoint**: `POST https://berich.cc/api/v1/chat/completions`
- **Models Catalogue**: `GET https://berich.cc/api/v1/models`
  - Returns available models with the real-time count of active worker keys (`active_pool_keys`).
  - Clients should filter for `active_pool_keys > 0` to select viable online candidate models.

### 3. Supply Dynamics & Constraints
- **Dynamic Catalogue (No Guaranteed Count)**: The model pool depends on community worker availability. There is no guaranteed fixed model count, no promise that any model is permanently online, and no default paid fallback key. If zero nodes are online for a model, requests are rejected; listing in the catalogue does not guarantee instantaneous availability.
- **Strictly Text Format & Tool Constraints**: The `content` field must be a plain text string. The gateway explicitly rejects `tools` and `tool_choice`, does not support `tool_calls` or function calling workflows, and rejects multimodal image/audio payloads.
- **SSE Buffering**: Current SSE streaming buffers the complete upstream response before chunking it to the client; it does not offer upstream token-by-token streaming.

---

## 📊 Quota Rules & VIP Privileges

### 1. Daily Quota Formula
- **Base Guest Quota**: 3,000 Tokens/day.
- **Online Contributor Quota**: While a worker node is verifiably online, the account receives a base of 100,000 Tokens/day, and can be higher via verified holdings: `max(100,000, verified holding quota)` Tokens/day.
- **Web3 Wallet Signature & Holding Quota**:
  - Requires Web3 wallet signature verification and balance confirmation. **Holding tokens alone never grants VIP or intraday access!**
  - Holding quota formula: `int(balance * 0.5)`.
  - Normal daily cap: `max(3,000, holding quota)`.
  - Balance >= 50,000 $BERICH: Quota floor of 25,000 Tokens/day: `max(25,000, holding quota)`; valid non-contributor VIP members may also receive a 25,000 floor.
  - **Important Rule: Online sharing quota and holding quota take the maximum (`max()`), NOT the sum!**
  - Benchmark Examples (the formula supports continuous intermediate balances, not fixed rigid tiers):
    - 0 $BERICH: 3,000 Tokens/day
    - 50,000 $BERICH: 25,000 Tokens/day
    - 200,000 $BERICH: 100,000 Tokens/day
    - 2,000,000 $BERICH: 1,000,000 Tokens/day
- **Quota Reset Time**: 08:00 Taiwan Time daily (00:00 UTC).
- **Offline Node State**: If a worker disconnects or its credential is revoked, online sharing quota is lost immediately, falling back to verified holdings quota or the base quota. Offline workers do not accumulate VIP days.

### 2. Taiwan Stock Market VIP Comparison Table
Authenticated members receive Taiwan Stock Intraday VIP while their node is actively online:

| Feature | Guest | VIP Member |
| :--- | :--- | :--- |
| Intraday AI Stock Picker | Stock tickers masked intraday, revealed after 15:00 close | Real-time unmasked stock tickers intraday |
| Live Position Tracking | Tickers masked intraday, revealed after 15:00 close | Real-time position entry, take-profit & stop-loss tracking |

### 3. Worker Credits & Incentives
- Registration or read-only verification yields no immediate rewards.
- Logged credits reflect actual successfully completed inference tasks settled by the backend; they do not guarantee onchain withdrawal, minting, or investment income.
- Token Contract (Robinhood): `0xf54e1870A77A2209d960470f2A787Cbf0046536C` ([Official Virtuals Page](https://app.virtuals.io/virtuals/144934); provided solely for technical identification; not financial or investment advice).

---

## 🛡️ End-to-End Conversation Encryption (`br_enc_v1` AEAD), Mechanics & Risk Disclosure

1. **Full Conversation Encryption (`br_enc_v1` AEAD) & Ephemeral RAM Zeroization**:
   - **Authenticated Payload Encryption**: Every task prompt (`/api/compute/tasks/claim`) and inference result (`/api/compute/tasks/submit`) is encrypted using the 100% Python stdlib `br_enc_v1` AEAD envelope (`HKDF-SHA256` key derivation + 128-bit random nonce + `SHA256-CTR` stream cipher + `HMAC-SHA256` Encrypt-then-MAC tag bound to `berich-e2ee-v1|{direction}|{task_id}|{node_id}` AAD), preventing cross-task replay and tampering.
   - **Encrypted In-Memory Queue & Immediate Wipe**: In-flight tasks are stored encrypted in server RAM using an ephemeral server key and are immediately wiped (`pop` + zeroization) as soon as the response is returned to the caller (zero database persistence, zero conversation logging).
   - **Local Zero-History & Injection Hardening**: The worker enforces strict regex validation on model identifiers (blocking `--` CLI flag injection), injects zero-history environment variables (`HISTFILE=/dev/null`, etc.), and never prints conversation plaintext or OAuth credentials to logs.
2. **Local CLI Execution & Authorization**: The worker relays tasks through existing authenticated CLIs. Official CLIs read their local configuration and credentials, and requests pass through community routing and upstream servers. While empty temporary working directories and `--tools ""` mitigate risk, **this is not full sandbox isolation and does not guarantee zero local file access**.
3. **Pre-Execution Idle Guard**: Idle Guard is an optional parameter (the page-generated command includes `--idle-only` by default with a 60-second threshold `--idle-threshold 60.0`). When enabled, the worker checks system idle state before claiming tasks and before invoking the CLI; detection failure or active user input pauses task claiming. **If a CLI task is already in progress, active mouse or keyboard movements will not immediately kill the running process**; the worker pauses further claiming after the active task finishes if user activity is detected. Without `--idle-only`, the worker processes tasks continuously.
4. **Operating System Support Differences**: macOS (`ioreg`) and Windows (`GetLastInputInfo`) provide native idle tracking. On Linux, idle detection returns `None`, meaning `--idle-only` will not claim tasks due to fail-closed safety; **Linux does not have fully supported idle-guard mode**.
5. **Service-Side Usage Estimates**: The backend service maintains a rolling 5-hour usage estimate to manage community pool capacity with a 75% soft limit, rather than local worker tracking of official quotas. This heuristic cannot query true upstream server balances and does not guarantee reserving 25% of your official quota.
6. **Pattern & Redaction Limits**: Built-in pattern filters and regular expression redaction mitigate risk but cannot guarantee absolute safety or complete de-identification.
7. **Terms of Service & No Ban Guarantee**: This open-source project is distributed compute research and cannot guarantee zero account-suspension risk. Upstream AI providers may update their Terms of Service at any time; users assume all operational risks.

---

## 🧪 Offline Simulation Check

You can run the offline test suite locally to verify code configuration and mock routing logic:

```bash
python3 prove_it_works.py
```

> **Important Notice**: This script is an offline mock inspection (does not connect to external networks or live upstream APIs) to verify fixtures and configuration. **It cannot prove zero backdoors, nor does it equal live CLI, Windows/official compatibility, or security certification.**
- **AST Static Inspection**: Validates standard library imports and syntax tree structure.
- **Pre-Execution & Parameter Checks**: Verifies idle-time reading logic, argument assembly, and CLI model flag-injection blocking.
- **Multi-Subscription Mounting Mock**: Simulates multi-provider registration and token stripping against a local mock server.
- **Encrypted Task Dispatch & Ephemeral Wipe Mock**: Simulates endpoint dispatch, `br_enc_v1` AEAD encryption/decryption, HMAC tamper rejection, and immediate post-completion memory wipe.
- **Failover Mock**: Tests 429 error classification and task queue re-insertion.
- **Pattern & Regex Redaction Tests**: Evaluates built-in safety keywords and regex masking routines.

---

## 📂 Repository Contents

| File | Description |
| :--- | :--- |
| [`berich_worker.py`](./berich_worker.py) | Main worker script: relays AI inference when idle to earn Taiwan Stock VIP while online |
| [`mock_gateway_server.py`](./mock_gateway_server.py) | Local test gateway: simulates API forwarding and proof reporting locally |
| [`prove_it_works.py`](./prove_it_works.py) | Offline simulation script: inspects test cases, configuration, and offline flow |
| [`.github/workflows/verify-proof.yml`](./.github/workflows/verify-proof.yml) | GitHub CI: executes offline simulation suite in virtual machines |
| [`LICENSE`](./LICENSE) | MIT License |

---

## ⭐ Star History

If this project helps you turn idle AI subscriptions into valuable compute, give us a **Star ⭐**!

[![Star History Chart](https://api.star-history.com/svg?repos=berich-protocol/berich-oauth-worker&type=Date)](https://star-history.com/#berich-protocol/berich-oauth-worker&Date)
