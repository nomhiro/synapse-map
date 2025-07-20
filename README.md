# AI Brainstorming System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.6.4-green.svg)](https://github.com/microsoft/autogen)

> 🤖 **Multi-Agent AI Brainstorming System with Real-time Chat Visualization**

AutoGenを使用した多エージェントAIブレインストーミングシステム。製品開発・サービス企画のアイデア出しを5つの専門AIエージェントが協力して行い、リアルタイムでCosmosDBに保存、Streamlitで可視化できます。

## ✨ 特徴

### 🎯 Multi-Agent Collaboration
- **5つの専門エージェント**が協力してブレインストーミング
- **創造的企画者** - 革新的なアイデアを提案
- **市場分析者** - 市場動向とニーズを分析  
- **技術検証者** - 技術的実現可能性を評価
- **事業評価者** - ビジネス的価値を検討
- **利用者代弁者** - ユーザー目線での意見

### 💾 Real-time Data Persistence
- **CosmosDB連携**: エージェントの発言をリアルタイムで保存
- **セッション管理**: ブレインストーミングの進行状況を追跡
- **メッセージ履歴**: 全ての会話を時系列で記録

### 📊 Interactive Visualization
- **Streamlit Dashboard**: リアルタイムチャット再現
- **セッション一覧**: 過去のブレインストーミング履歴
- **進行状況表示**: 実行中セッションの自動更新

### 🛠️ Developer Friendly
- **モジュラー設計**: カスタマイズ可能なアーキテクチャ
- **環境別設定**: development/production設定分離
- **詳細ログ**: デバッグとモニタリング機能
- **Unicode対応**: 日本語テキストの安全な処理

## ディレクトリ構成

```
├── src/
│   ├── agents/          # エージェント定義
│   ├── config/          # 設定管理
│   ├── core/            # 核となるビジネスロジック
│   ├── utils/           # 共通ユーティリティ
│   └── main.py          # メインエントリポイント
├── configs/             # 設定ファイル
├── scripts/             # 実行スクリプト
├── tests/               # テストファイル
├── logs/                # ログファイル
└── docs/                # ドキュメント
```

## 🚀 クイックスタート

### 前提条件

- Python 3.11以上
- Azure CosmosDB アカウント（オプション）
- OpenAI API キー または Azure OpenAI

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/your-username/ai-brainstorming-system.git
cd ai-brainstorming-system

# 仮想環境作成
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 依存関係インストール
pip install -r requirements.txt
```

### 設定

```bash
# 環境変数ファイルをコピー
cp .env.example .env

# .envファイルを編集してAPIキーを設定
# AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
# AZURE_OPENAI_API_KEY=your_azure_openai_api_key
# COSMOSDB_ENABLED=true  # CosmosDB使用時
# COSMOSDB_ENDPOINT=your_cosmosdb_endpoint
# COSMOSDB_KEY=your_cosmosdb_key
```

### 実行

```bash
# Streamlit統合ダッシュボード起動（推奨）
run_chat_viewer.bat  # Windows
./run_chat_viewer.sh  # Linux/Mac
# http://localhost:8501 でアクセス

# コマンドライン実行（従来方式）
python src/main.py
```

## 📖 使い方

### 1. Streamlit統合ダッシュボード（推奨）

```bash
# ダッシュボード起動
run_chat_viewer.bat  # Windows
./run_chat_viewer.sh  # Linux/Mac

# ブラウザで http://localhost:8501 にアクセス
```

#### 🧠 ライブブレインストーミング
1. **タスク入力**: 検討したいアイデア・課題を入力
2. **システムチェック**: Azure OpenAI接続確認
3. **実行開始**: 🚀ボタンでブレインストーミング開始
4. **リアルタイム表示**: AIエージェントの会話をライブ監視

#### 📋 セッション一覧
- **過去履歴**: 過去のブレインストーミング結果を確認
- **ステータス**: 🟡実行中 / 🟢完了 / 🔴失敗
- **詳細表示**: セッション選択で詳細チャット表示

### 2. コマンドライン実行（従来方式）

```bash
# インタラクティブモード
python src/main.py

# タスク指定モード
python src/main.py --task "新しいフィットネスアプリのアイデア検討"

# 環境別実行
python scripts/run_development.py  # 開発環境
python scripts/run_production.py   # 本番環境

# ヘルスチェック
python src/main.py --health-check
```

### 3. データ管理

- **リアルタイム保存**: CosmosDBへの即座保存（オプション）
- **ローカル保存**: JSONファイルへの自動保存
- **履歴検索**: 過去セッションの検索・参照

## 設定

### 環境変数

- `AOAI_DEPLOYMENT_CHAT`: Azure OpenAI チャット用デプロイメント名
- `AOAI_DEPLOYMENT_REASONING`: Azure OpenAI 推論用デプロイメント名
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI エンドポイント
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API キー

### 設定ファイル

- `configs/default.yaml`: デフォルト設定
- `configs/development.yaml`: 開発環境設定
- `configs/production.yaml`: 本番環境設定

## エージェント

### 1. Creative Planner (創造的企画者)
- 革新的なアイデアの提案
- 既存の枠にとらわれない発想

### 2. Market Analyst (市場分析者)
- 市場動向の分析
- 競合分析と差別化戦略

### 3. Technical Validator (技術検証者)
- 技術的実現可能性の評価
- 開発リスクの分析

### 4. Business Evaluator (ビジネス評価者)
- 収益性の評価
- 投資対効果の分析

### 5. User Advocate (ユーザー体験専門家)
- ユーザビリティの評価
- 顧客満足度の分析

### 6. Reflection Agent (リフレクション)
- 会話の振り返り
- 新しいトピックの提案

## 開発

### テストの実行

```bash
pytest
```

### コードフォーマット

```bash
black src/
isort src/
```

### 型チェック

```bash
mypy src/
```

## ライセンス

MIT License