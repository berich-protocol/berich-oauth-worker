# BeRich OAuth Worker (`berich-oauth-worker`)

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

[![GitHub Stars](https://img.shields.io/github/stars/berich-protocol/berich-oauth-worker?style=for-the-badge&logo=github&color=fbbf24)](https://github.com/berich-protocol/berich-oauth-worker/stargazers)
[![100% Python Stdlib](https://img.shields.io/badge/Python-100%25_内置标准库_(免装依赖)-10b981?style=for-the-badge)](./prove_it_works.py)
[![macOS | Windows | Linux](https://img.shields.io/badge/支持系统-macOS_%7C_Windows_%7C_Linux-3b82f6?style=for-the-badge)](./.github/workflows/verify-proof.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](./LICENSE)

> **一句话看懂这个项目：**  
> 把你每个月花 \$20 美元订阅、但睡觉或离开电脑时根本用不完的 **Claude Pro/Max、ChatGPT Plus/Pro、Google AI (Gemini)** 闲置额度分享给社区，**在线期间自动免费享 [BeRich (`https://berich.cc`)](https://berich.cc) 全站台股盘中 VIP，并获得每日 `100,000 Tokens` 跨模型共享 AI 互助额度（可自由切换调用池内 8 大顶尖模型）；不想开机跑节点的人，则可在 [Virtuals 市场](https://app.virtuals.io/virtuals/144796) 持有 `$BRICH` 并通过 Web3 钱包签名验证，免开机永久解锁台股 VIP 与每日共享 AI 额度！**

---

## 🔄 双轨权益机制：分享闲置 AI 订阅 vs. 持币签名解锁

**[BeRich (`https://berich.cc/compute`)](https://berich.cc/compute)** 提供两种开通全站台股盘中 VIP 与跨模型共享 AI 额度的方式：

1. **💻 方式一：分享闲置 AI 订阅（免费互助通道）**
   - 离开电脑时运行本开源节点，分享闲置的 Claude / ChatGPT / Gemini 订阅额度。
   - **节点保持在线期间**：自动免费开通 **BeRich 全站台股盘中 VIP**，并享每日 **`100,000 Tokens` 跨模型共享 AI 互助额度**（例如你只有订阅 Claude，分享后在 Cursor / Cline 也能免费切换调用池内的 Google 4 Argon、GPT-6 Astra 等全系列模型）。
2. **🔐 方式二：钱包持有 `$BRICH` 并完成签名验证（免开机通道）**
   - 直接在 **[Virtuals 官方市场 (`https://app.virtuals.io/virtuals/144796`)](https://app.virtuals.io/virtuals/144796)** 买入 **`$BRICH` 代币**放在自己的 Base 链钱包（免质押锁仓、免转账）。
   - **强制 Web3 钱包签名验证 (`personal_sign` / EIP-191)**：为防止任何人拿链上公开地址冒名绑定，绑定钱包时必须通过 MetaMask / Coinbase Wallet / OKX Wallet 完成一次性挑战码签名（零 Gas 费、不涉及任何交易授权）。
   - **按持币量解锁共享 AI 额度**：已签名验证之钱包每持有 **`1 枚 $BRICH`** 即解锁每日 **`0.5 Tokens`** 的共享 AI 额度（未持币每日试用 3,000 Tokens；持满 200 万枚享每日 100 万 Tokens）。
   - **持满 50,000 枚 `$BRICH`（5 万枚）**：每日享 **25,000 Tokens** 共享 AI 额度，**同时免开机永久解锁 `https://berich.cc` 全站台股盘中 VIP**！

---

## 🤖 支持跨模型互助调用之 8 大顶尖模型 (`/api/v1/chat/completions`)

通过共享池聚合网关（兼容 OpenAI SDK、Cursor、Cline），可一键切换调用三大厂牌共 8 款主力模型：
- **Google**：`gemini-4-argon` (`Google 4 Argon`)、`gemini-3.8-flash`
- **Anthropic**：`claude-opus-5-5`、`claude-sonnet-5-5`
- **OpenAI**：`gpt-6-astra`、`gpt-6.1-sol`、`gpt-5.6-terra`、`gpt-6-luna`

---

## 🛡️ 为什么 100% 安全？（三大白话保证）

1. **不用交出 API Key，不碰你的账号密码**
   - 你只要在自己电脑终端输入 `claude login`、`codex login` 或 `gemini` 完成官方登录即可，我们不收、也看不到你的账密与付费密钥。
2. **你在用电脑时它就休息，你离开电脑它才工作**
   - 内置鼠标与键盘侦测：只要你一动鼠标或打字，程序在几毫秒内立刻暂停礼让你；而且最多只会用掉 75% 额度，永远保留 25% 以上给你自己用。
3. **不读你电脑里任何文件，随时 `Ctrl+C` 就关掉**
   - 整支程序只用 Python 内置标准库（免装任何依赖），里面**连一个 `open()` 读档指令都没有**，并强制加上 `--tools ""` 关闭所有工具权限，绝对碰不到你的个人文件。

---

## 🚀 30 秒极简三步开通在线 VIP 与跨模型互助额度

### 第 1 步：在终端登录你有的 AI 会员（有哪个登哪个）
- **macOS / Linux (Terminal)**：
  ```bash
  claude login && codex login && gemini
  ```
- **Windows (PowerShell)**：
  ```powershell
  claude login; codex login; gemini
  ```

### 第 2 步：粘贴一行启动指令并点击「验证连线」
前往 **[`https://berich.cc/compute`](https://berich.cc/compute)**：
1. 勾选你有的 AI 会员（可多选）。
2. 复制页面上的启动指令粘贴到终端运行，再点一下页面上的 **「我已执行指令，验证连线」**。

### 第 3 步：立即使用台股盘中 VIP 与跨模型共享 AI 额度
只要节点保持在线，即可立即在 `berich.cc` 查看盘中实时选股与实盘仓位，并在第 2 个页签领取专属聚合 API Key，在 Cursor / Cline 或自己的程序中使用每日 `100,000 Tokens` 互助额度切换调用池内 8 大模型！

---

## ⚡ 3 秒钟自己验证安全性（免联网自动检查）

打开终端直接运行这行指令，3 秒钟自动检查完 6 项安全铁证：

```bash
python3 prove_it_works.py
```

1. **代码零后门检查**：自动扫描 `berich_worker.py`，证明 0 外部依赖、0 `open()` 读档指令。
2. **双平台与沙箱检查**：确认 macOS / Windows 动鼠标即暂停，且强制开启 `--tools ""` 安全限制。
3. **多账号同时挂载**：实测同时挂载 Claude、ChatGPT、Gemini 三大订阅。
4. **在线 VIP 与互助额度结算**：实测完成跨模型 AI 分析任务后，自动记录共享贡献并启用在线 VIP 与互助额度。
5. **跨节点自动接力**：当你动鼠标暂停或额度用完时，任务自动交棒给下一台电脑，不中断对话。
6. **防封号与隐私保护**：自动拦截违规问题，并自动把邮箱、电话、密钥打码隐藏。

---

## 💎 关于 `$BRICH` 代币信息

- **代币代号 (Ticker)**：`$BRICH`
- **Virtuals 官方交易市场**：[`https://app.virtuals.io/virtuals/144796`](https://app.virtuals.io/virtuals/144796)
- **Base 链合约地址**：`0x86D4854150c11b606081f8101Bf239A0c110999E`
- **代币双重赋能（需完成 Web3 钱包 `personal_sign` 签名验证）**：
  1. **共享 AI 额度**：每持有 `1 枚 $BRICH` 解锁每日 `0.5 Tokens` 共享 AI 额度（5 万枚享每日 25,000 Tokens；200 万枚享每日 100 万 Tokens）。
  2. **解锁台股盘中 VIP**：钱包持满 **50,000 枚 `$BRICH`**（免锁仓，随时可买卖）即可免开机永久解锁 `https://berich.cc` 全站台股盘中 VIP。

---

## 📂 文件说明

| 文件 | 白话用途 |
| :--- | :--- |
| [`berich_worker.py`](./berich_worker.py) | 主程序：在你离开电脑时分享闲置 AI 额度，在线自动享台股 VIP 与跨模型共享 AI 互助额度 |
| [`mock_gateway_server.py`](./mock_gateway_server.py) | 本地测试服务器：让你在自己电脑上模拟测试跨模型 API 转发与互助贡献结算 |
| [`prove_it_works.py`](./prove_it_works.py) | 3 秒安全验证脚本：不用连外网，自动帮你检查代码有没有后门 |
| [`.github/workflows/verify-proof.yml`](./.github/workflows/verify-proof.yml) | GitHub 自动测试：每次更新自动在 Mac / Windows / Linux 跑安全检查 |
| [`LICENSE`](./LICENSE) | MIT 开源许可证 |

---

## ⭐ Star History（累积星标趋势图）

如果这个项目能帮你把闲置的 AI 订阅额度变成跨模型互助额度与台股 VIP 权益，欢迎点右上角 **Star ⭐** 支持我们！

[![Star History Chart](https://api.star-history.com/svg?repos=berich-protocol/berich-oauth-worker&type=Date)](https://star-history.com/#berich-protocol/berich-oauth-worker&Date)
