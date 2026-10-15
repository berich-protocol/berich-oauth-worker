# BeRich OAuth Worker (`berich-oauth-worker`)

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

[![GitHub Stars](https://img.shields.io/github/stars/berich-protocol/berich-oauth-worker?style=for-the-badge&logo=github&color=fbbf24)](https://github.com/berich-protocol/berich-oauth-worker/stargazers)
[![100% Python Stdlib](https://img.shields.io/badge/Python-100%25_内置标准库_(免装依赖)-10b981?style=for-the-badge)](./prove_it_works.py)
[![macOS | Windows](https://img.shields.io/badge/支持系统-macOS_%7C_Windows-3b82f6?style=for-the-badge)](./.github/workflows/verify-proof.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](./LICENSE)

> **项目核心说明：**
> 把电脑上闲置的 AI 月费订阅（Claude Pro/Max、ChatGPT Plus/Pro、Google Gemini）通过本机已登录的官方 CLI 分享给社区（无需提供 API Key），**在节点保持在线期间获取 [BeRich (`https://berich.cc`)](https://berich.cc) 台股盘中 VIP 特权与跨模型互助额度**，并将社区算力汇聚为**标准 OpenAI 兼容 API 网关 (`/v1/chat/completions`)**。

---

## 🔄 核心功能与两大用途

前往 **[`https://berich.cc/compute`](https://berich.cc/compute)** 即可查看与操作两项主要功能标签页：

### 1. 标签页：“分享订阅换 VIP”（`分享訂閱換 VIP`）
- **分享闲置订阅**：通过本机官方 CLI 转发推理任务。
- **台股盘中 VIP 特权**：保持 Worker 节点在线，已登录之 BeRich 正式会员在线期间自动享有台股盘中 VIP 特权（盘中即时显示真实选股代码与实盘持仓追踪）。
- **跨模型互助额度**：节点在线期间基础享有每日 100,000 Tokens 跨模型互助 API 额度（验证持币额度若更高则取较大者）。
- **⚠️ 权益归属说明**：台股盘中 VIP 为实际登录会员专属权益。请先在 BeRich 登录账号后再获取专属命令启动节点以完成归户；若以匿名会话启动节点，该会话可获得共享 API 互助额度，但匿名访客无法继承台股看盘之会员 VIP 特权。

### 2. 标签页：“免费用 AI（例如龙虾 OpenClaw）”（`免費用 AI（例如龍蝦 OpenClaw）`）
- **标准 OpenAI 兼容 API 网关**：全网节点汇聚成标准 API 网关（`https://berich.cc/api/v1`）。
- **外部客户端调用示例**：用户可将 Base URL 与网关 API Key 配置至支持自定义 OpenAI 端点的客户端（例如 **OpenClaw（龙虾）**）进行纯文本对话生成。
- **⚠️ 客户端限制声明**：OpenClaw 仅作为兼容客户端的调用示例参考。本网关目前仅支持纯文本格式，不支持 `tools` / `tool_choice`、Function Calling 工作流与多模态输入，不代表支持完整的 OpenClaw 自动化 Agent 或工具执行。

---

## 🛠️ 前置需求与启动方式

### 前置需求
1. **Python 环境**：需安装 Python（CI 测试环境为 Python 3.11；Worker 主程序 100% 采用 Python 内置标准库，无需 `pip install` 安装任何第三方依赖）。
2. **官方 AI CLI 工具**：本机需预先安装并完成官方授权登录：
   - **Claude Pro / Max**：`claude login`
   - **ChatGPT Plus / Pro**：`codex login`
   - **Google Gemini**：`gemini`
   - 若不确定如何安装或登录，请参考各 CLI 工具官方现行文档操作。

### 启动流程
1. 前往 **[`https://berich.cc/compute`](https://berich.cc/compute)** 的“**分享訂閱換 VIP**”标签页。若需台股 VIP，请先在网站登录会员。
2. 勾选本机已具备的订阅项目与操作系统。
3. 点击页面上的 **“取得本機啟動指令”** 按钮，复制页面生成的完整命令。
4. 将整串命令直接粘贴至本机终端运行，**请勿自行修改参数或替换节点 ID**（网页命令会自动绑定带有凭证的 Node ID、提供者列表与可选的闲置避让参数）。
5. **凭证与密钥隔离**：`bw_oauth_...` 为 Worker 节点通信凭证，与外部调用所使用的 API Key（`sk-berich-...`）互相独立，请勿对外公开或分享您的启动命令与私有密钥。
6. **程序更新**：当 Worker 代码更新时，请终止当前运行进程并重新获取最新启动命令以加载新版本。

---

## 🔑 自动核发 API 密钥与模型目录

### 1. 自动核发与密钥管理
- 具备签名或登录之拥有者启动并成功注册真实 Worker 后，服务器将自动创建或复用专属 API 网关密钥（`sk-berich-...`）。
- 重复连接或重启 Worker 会保留原密钥与当日使用额度，不会在每次重连时自动轮换。
- 终端与注册响应仅显示掩码密钥（如 `sk-berich-...***`）、API Base URL 与当前在线模型。完整密钥可由已登录会员或**同一服务器签署 Cookie 之匿名浏览器会话**在 `https://berich.cc/compute` 页面查看复制（匿名身份由服务器签署浏览器 Cookie 识别，无需强制钱包签名）。

### 2. API 调用规范与端点
- **API Base URL**：`https://berich.cc/api/v1`
- **对话补全端点**：`POST https://berich.cc/api/v1/chat/completions`
- **模型目录端点**：`GET https://berich.cc/api/v1/models`
  - 返回目录包含每个模型的即时在库密钥数 `active_pool_keys`。
  - 客户端应筛选 `active_pool_keys > 0` 作为当前实际可用的候选模型。

### 3. 动态供应与调用限制
- **无固定数量或永久在线保证**：聚合池依赖社区节点动态在线状态，不保证固定模型数量，亦无付费环境密钥自动兜底。若某模型当下无在线节点承接，请求将直接被拒绝；模型出现在目录中不代表当下百分之百可用。
- **纯文本格式与工具限制**：对话消息 `content` 必须为纯文本字符串；网关明确拒绝 `tools` 与 `tool_choice` 参数，不支持 `tool_calls` 与 Function Calling 工具工作流，亦不支持图片/音频等多模态内容。
- **SSE 流式传输特性**：现行 SSE 流式传输采用后端完整获取回答后分块推送到客户端的机制，非上游逐字 Token 即时流式输出。

---

## 📊 额度规则与 VIP 权益

### 1. 每日 API 额度计算公式
- **基础试用额度**：普通访客每日 3,000 Tokens。
- **在线贡献者互助通道**：节点真实保持在线期间，额度基础为 100,000 Tokens/日；若经验证之持币额度更高则取较大者：`max(100,000, 验证后持币额度)` Tokens/日。
- **Web3 钱包签名与持币额度**：
  - 需通过 Web3 钱包完成签名验证与余额确认。**单纯在钱包持有代币绝不直接享有 VIP 或盘中功能！**
  - 持币额度计算公式：`int(balance * 0.5)`。
  - 一般情况下每日额度上限：`max(3,000, 持币额度)`。
  - 若持币量达 50,000 $BRICH 以上：每日额度下限为 25,000 Tokens，即 `max(25,000, 持币额度)`；具备有效非贡献者 VIP 会员亦享有 25,000 额度下限。
  - **重要规则：共享在线额度与持币额度采取“两者取较大者 (`max`)”，而非叠加相加！**
  - 基准试算示例（公式支持任意中间余额，非固定阶梯限制）：
    - 0 $BRICH：3,000 Tokens/日
    - 50,000 $BRICH：25,000 Tokens/日
    - 200,000 $BRICH：100,000 Tokens/日
    - 2,000,000 $BRICH：1,000,000 Tokens/日
- **额度重置时间**：台湾时间每日 08:00（UTC 00:00）。
- **离线状态处理**：节点离线或凭证撤销时，立即失去在线共享资格，额度回退至持币验证或基础额度；不累积离线 VIP 天数。

### 2. 台股盘中 VIP 权益对照表
在线期间已登录会员自动开通台股盘中 VIP：

| 项目 | 普通访客 | VIP 会员 |
| :--- | :--- | :--- |
| 盘中 AI 选股 | 盘中隐藏代码，15:00 收盘后公开 | 盘中即时显示真实股票代码 |
| 实盘持仓追踪 | 盘中隐藏代码，15:00 收盘后公开 | 盘中同步查看建仓与止盈止损 |

### 3. 节点贡献点数与激励
- 节点注册或只读验证不会产生即时奖励。
- 终端显示之贡献点数依据实际成功承接并完成的推理任务结算，不承诺保证链上提领、铸造或投资收益。
- 代币合约地址（Base 链）：`0x86D4854150c11b606081f8101Bf239A0c110999E`（仅供技术集成识别，不构成任何财务或投资建议）。

---

## 🛡️ 运作机制、限制与风险披露

1. **本机 CLI 调用与授权传输**：Worker 通过本机已登录之官方 CLI 转发推理。官方 CLI 运行时仍会读取其本机登录凭证与配置，请求会经过调度服务与官方上游服务器。程序通过指定空白暂存目录与禁用工具参数降低风险，但**不等于完整系统沙箱隔离，亦不保证无本机文件读取**。
2. **前置闲置检查机制 (Idle Guard)**：闲置避让为选配参数（网页命令默认带入 `--idle-only`，默认阈值为 60 秒 `--idle-threshold 60.0`）。启用时，Worker 在任务领取前与调用 CLI 前双重检查系统闲置状态；检测失败或用户活跃时暂停领单。**若 CLI 已在执行中，移动鼠标或键盘不会即时强制终止正在运行中的 CLI 进程**；待当前任务完成后，若检测到用户正在操作电脑，才会暂停领取新任务。若未加上 `--idle-only`，Worker 将处于全时段接单状态。
3. **跨平台闲置检测差异**：macOS 与 Windows 支持原生闲置读取；Linux 系统目前闲置检测返回 `None`，若在 Linux 启用 `--idle-only` 将因安全保护机制而无法领取任务，**Linux 不支持完整闲置避让模式**。
4. **服务端用量推估机制**：服务端后端维持 5 小时滚动用量推估，用于社区池容量调度并设有 75% 软上限保护，非本机 Worker 直接追踪官方额度。此数值为服务端推估，无法查询官方后端真实剩余额度，亦不保证保留 25% 官方额度。
5. **关键词过滤与脱敏局限**：内置关键词过滤与正则表达式脱敏仅为辅助过滤手段，无法保证绝对安全、不保证完全去标识化。
6. **服务条款与无封号保证 (No Ban Guarantee)**：本项目为开源分布式计算技术实现，无法保证零封号风险。各 AI 供应商随时可能更新服务条款，用户须自行评估并承担使用账号的相关风险。

---

## 🧪 离线模拟检查 (Offline Simulation Check)

您可在本机终端运行模拟检查脚本，检验代码配置与离线转发逻辑：

```bash
python3 prove_it_works.py
```

> **重要说明**：此脚本为纯本机离线 mock 测试与静态配置检查（不连外网、不打真实上游），仅用于验证受测范例配置，**不能证明零后门，亦不等于真实 CLI、Windows/官方兼容性或安全认证**。
- **AST 语法树静态检查**：检查 `berich_worker.py` 标准库引用与语法结构。
- **前置闲置与参数检查**：检查系统闲置时间读取逻辑与 CLI 参数组装。
- **多订阅挂载模拟**：在本地 mock 服务器验证多供应商数据结构。
- **任务分发与完单模拟**：模拟端点派单与首笔完单状态更新。
- **额度耗尽转派模拟**：测试 429 错误分类与任务重回队列逻辑。
- **文字与脱敏规则测试**：测试内置安全过滤词与 regex 遮蔽效果。

---

## 📂 文件清单

| 文件 | 实际用途 |
| :--- | :--- |
| [`berich_worker.py`](./berich_worker.py) | 主程序：在电脑闲置时转发 AI 任务，在线期间享有 BeRich 台股盘中 VIP |
| [`mock_gateway_server.py`](./mock_gateway_server.py) | 本机测试服务器：在本地环境模拟测试 API 转发与任务回报 |
| [`prove_it_works.py`](./prove_it_works.py) | 离线模拟检查脚本：在本地验证受测范例、参数配置与离线转发逻辑 |
| [`.github/workflows/verify-proof.yml`](./.github/workflows/verify-proof.yml) | GitHub CI：在虚拟机运行离线模拟检查 |
| [`LICENSE`](./LICENSE) | MIT 开源授权条款 |

---

## ⭐ Star History

如果这个项目能帮你把闲置的 AI 订阅额度转化为实质价值，欢迎点右上角 **Star ⭐** 支持我们！

[![Star History Chart](https://api.star-history.com/svg?repos=berich-protocol/berich-oauth-worker&type=Date)](https://star-history.com/#berich-protocol/berich-oauth-worker&Date)
