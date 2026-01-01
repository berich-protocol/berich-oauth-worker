# BeRich OAuth Worker (`berich-oauth-worker`)

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

[![GitHub Stars](https://img.shields.io/github/stars/berich-protocol/berich-oauth-worker?style=for-the-badge&logo=github&color=fbbf24)](https://github.com/berich-protocol/berich-oauth-worker/stargazers)
[![100% Python Stdlib](https://img.shields.io/badge/Python-100%25_標準ライブラリ_(依存関係ゼロ)-10b981?style=for-the-badge)](./prove_it_works.py)
[![macOS | Windows | Linux](https://img.shields.io/badge/対応OS-macOS_%7C_Windows_%7C_Linux-3b82f6?style=for-the-badge)](./.github/workflows/verify-proof.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](./LICENSE)

> **ひとことで言うと：**  
> 毎月 \$20 払っているのに、寝ている間や離席中に余っている **Claude Pro/Max、ChatGPT Plus/Pro、Google AI (Gemini)** の空き枠をシェアすると、**オンライン稼働中は [BeRich (`https://berich.cc`)](https://berich.cc) の台湾株場中 VIP が自動解放され、さらに毎日 `100,000 Tokens` のクロスモデル共有 AI 枠（8 大最新モデルを自由に呼び出し可能）が無料で使えます。ノードを稼働させずに常時利用したい方は、[Virtuals 市場](https://app.virtuals.io/virtuals/144796) で `$BRICH` を保有し、Web3 ウォレット署名認証を行うことで永久 VIP と毎日共有 AI 枠を解放できます！**

---

## 🔄 2 つの解放ルート：空き枠シェア vs. `$BRICH` 保有＆ウォレット署名認証

**[BeRich (`https://berich.cc/compute`)](https://berich.cc/compute)** では、以下の 2 つの方法で台湾株 VIP と共有 AI 枠を利用できます：

1. **💻 ルート 1：空き AI サブスクをシェア（無料相互利用ルート）**
   - 離席中にこのオープンソースノードを起動し、Claude / ChatGPT / Gemini の空き枠をシェアします。
   - **オンライン稼働中**：**BeRich の台湾株場中 VIP が自動解放**され、さらに毎日 **`100,000 Tokens` のクロスモデル共有 AI 枠**が付与されます（例：Claude のみ契約していても、Cursor や Cline から Google 4 Argon や GPT-6 Astra など全 8 モデルを呼び出し可能）。
2. **🔐 ルート 2：ウォレットで `$BRICH` を保有し署名認証（PC 稼働不要ルート）**
   - **[Virtuals 公式市場 (`https://app.virtuals.io/virtuals/144796`)](https://app.virtuals.io/virtuals/144796)** で **`$BRICH` トークン**を購入し、ご自身の Base ウォレットに保有します（ロックアップ不要・送金不要）。
   - **Web3 ウォレット署名認証 (`personal_sign` / EIP-191)**：ブロックチェーン上の公開アドレスのなりすましを防ぐため、MetaMask / Coinbase Wallet / OKX Wallet でのワンタイム署名認証が必須です（ガス代ゼロ・送金権限不要）。
   - **保有量に応じて共有 AI 枠を解放**：署名認証済みウォレットに **`1 $BRICH`** 保有するごとに、毎日 **`0.5 Tokens`** の共有 AI 枠（未保有は毎日 3,000 Tokens お試し；200 万 `$BRICH` で毎日 100 万 Tokens）が解放されます。
   - **50,000 `$BRICH` 保有**：毎日 **25,000 Tokens** の共有 AI 枠が解放されると同時に、**PC を起動しなくても `https://berich.cc` の台湾株場中 VIP が永久解放**されます！

---

## 🤖 対応する 8 大最新 AI モデル (`/api/v1/chat/completions`)

OpenAI 互換ゲートウェイ（Cursor、Cline、Python SDK 対応）から以下の 8 モデルを自由に切り替え可能です：
- **Google**：`gemini-4-argon` (`Google 4 Argon`)、`gemini-3.8-flash`
- **Anthropic**：`claude-opus-5-5`、`claude-sonnet-5-5`
- **OpenAI**：`gpt-6-astra`、`gpt-6.1-sol`、`gpt-5.6-terra`、`gpt-6-luna`

---

## 🛡️ なぜ 100% 安全なのか？（3 つの約束）

1. **API キー不要・パスワードも一切預かりません**
   - ご自身のパソコンで公式コマンド（`claude login`、`codex login`、`gemini`）でログインするだけ。パスワードや課金キーを入力する必要はありません。
2. **パソコンを使っている時は自動で休み、離れた時だけ動きます**
   - マウスやキーボードを動かした瞬間にミリ秒単位で自動一時停止します。また、最大でも枠の 75% までしか使わず、常に 25% 以上をあなた自身の利用分として残します。
3. **パソコン内のファイルは一切読みません（`Ctrl+C` でいつでも停止）**
   - Python 標準ライブラリのみで書かれており（追加インストール不要）、**ファイルを開く `open()` 命令すら 1 つもありません**。`--tools ""` でツール権限も完全ロックされているため、個人ファイルには一切触れられません。

---

## 🚀 カンタン 3 ステップでオンライン VIP ＆クロスモデル AI 枠を解放

### ステップ 1：ターミナルでお持ちの AI にログイン
- **macOS / Linux (Terminal)**：
  ```bash
  claude login && codex login && gemini
  ```
- **Windows (PowerShell)**：
  ```powershell
  claude login; codex login; gemini
  ```

### ステップ 2：1 行コマンドを貼り付けて「接続確認」をクリック
**[`https://berich.cc/compute`](https://berich.cc/compute)** にアクセス：
1. お持ちの AI サブスクにチェックを入れます。
2. 画面の起動コマンドをターミナルに貼り付けて実行し、画面の **「接続を確認する」** ボタンを押せばスタート！

### ステップ 3：台湾株 VIP とクロスモデル共有 AI 枠をすぐ利用
ノードがオンラインの間、`https://berich.cc` の場中リアルタイム銘柄やポジションを閲覧でき、さらに専用 API キーを使って毎日 `100,000 Tokens` の相互利用枠で全 8 モデルを呼び出せます！

---

## ⚡ 3 秒で安全性を自分でチェック（オフライン実行）

ターミナルで以下のコマンドを実行すると、ネット接続なしで 6 つの安全チェックが 3 秒で完了します：

```bash
python3 prove_it_works.py
```

1. **バックドアゼロ検査**：`berich_worker.py` に外部パッケージや `open()` ファイル読み取りがゼロであることを証明。
2. **離席検知＆サンドボックス検査**：マウス操作での即座停止と `--tools ""` 安全ロックを確認。
3. **複数サブスク同時接続**：Claude、ChatGPT、Gemini の同時稼働を確認。
4. **オンライン VIP ＆相互利用枠の確認**：AI 分析タスク完了後に貢献記録とオンライン VIP・共有 AI 枠の解放を確認。
5. **自動バトンタッチ**：マウスを動かした際、別のパソコンへ自動で処理が引き継がれることを確認。
6. **アカウント保護＆個人情報マスク**：規約違反プロンプトを遮断し、メールや電話番号を自動で伏せ字化。

---

## 💎 `$BRICH` トークンについて

- **トークンシンボル**：`$BRICH`
- **Virtuals 公式ページ**：[`https://app.virtuals.io/virtuals/144796`](https://app.virtuals.io/virtuals/144796)
- **Base コントラクトアドレス**：`0x86D4854150c11b606081f8101Bf239A0c110999E`
- **2 つのユーティリティ（Web3 ウォレット `personal_sign` 署名認証が必要）**：
  1. **共有 AI 枠の利用**：`1 $BRICH` 保有ごとに毎日 `0.5 Tokens` の共有 AI 枠を解放（`50,000 $BRICH` で毎日 25,000 Tokens；`2,000,000 $BRICH` で毎日 100 万 Tokens）。
  2. **永久 VIP 解放**：署名認証済みウォレットに **50,000 `$BRICH`** を保有（ロックアップ不要、いつでも売買可能）するだけで `https://berich.cc` の場中 VIP が永久解放。

---

## 📂 ファイル一覧

| ファイル | 役割 |
| :--- | :--- |
| [`berich_worker.py`](./berich_worker.py) | メインプログラム：離席中に AI の空き枠をシェアしてオンライン中の VIP とクロスモデル共有 AI 枠を解放 |
| [`mock_gateway_server.py`](./mock_gateway_server.py) | ローカルテスト用サーバー：ご自身の PC 上でマルチモデル転送と動作をテストできる |
| [`prove_it_works.py`](./prove_it_works.py) | 3 秒安全チェッカー：オフラインで 6 つのセキュリティ検証を自動実行 |
| [`.github/workflows/verify-proof.yml`](./.github/workflows/verify-proof.yml) | GitHub Actions：Mac / Windows / Linux で自動テストを実行 |
| [`LICENSE`](./LICENSE) | MIT オープンソースライセンス |

---

## ⭐ Star History

このプロジェクトが AI 空き枠の相互活用に役立ったら、ぜひ右上の **Star ⭐** を押して応援してください！

[![Star History Chart](https://api.star-history.com/svg?repos=berich-protocol/berich-oauth-worker&type=Date)](https://star-history.com/#berich-protocol/berich-oauth-worker&Date)
