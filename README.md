# AI Brainstorming System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.6.4-green.svg)](https://github.com/microsoft/autogen)

> 🤖 **Multi-Agent AI Brainstorming System with Real-time Chat Visualization**

AutoGenを使用した多エージェントAIブレインストーミングシステム。製品開発・サービス企画のアイデア出しを5つの専門AIエージェントが協力して行い、リアルタイムでCosmosDBに保存、Streamlitで可視化できます。

https://youtu.be/riaKDAVPWmk

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
│   ├── core/            # 核となるビジネスロジック
│   │   ├── session_manager.py    # セッション管理
│   │   ├── cosmosdb_manager.py   # CosmosDB連携
│   │   └── settings.py           # 設定管理
│   ├── web/             # Webアプリケーション
│   │   ├── streamlit_app.py      # Streamlitメインアプリ
│   │   ├── autogen_runner.py     # AutoGen統合アダプター
│   │   └── cosmosdb_reader.py    # データ読み取り
│   ├── utils/           # 共通ユーティリティ
│   └── main.py          # コマンドライン実行
├── blog/                # 技術ブログ記事
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
streamlit run src/web/streamlit_app.py
# または
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
streamlit run src/web/streamlit_app.py
# または
run_chat_viewer.bat  # Windows
./run_chat_viewer.sh  # Linux/Mac

# ブラウザで http://localhost:8501 にアクセス
```

#### 🧠 ライブブレインストーミング
1. **タスク入力**: 検討したいアイデア・課題を入力
2. **システムチェック**: Azure OpenAI接続確認
3. **実行開始**: 🚀ボタンでブレインストーミング開始
4. **リアルタイム表示**: AIエージェントの会話をライブ監視
5. **表示制御**: 🧹画面クリア、🔄自動/手動更新の切り替え

#### 📋 セッション一覧
- **過去履歴**: 過去のブレインストーミング結果を確認
- **ステータス**: 🟡実行中 / 🟢完了 / 🔴失敗
- **詳細表示**: セッション選択で詳細チャット表示
- **表示管理**: 🧹画面クリア、🔄更新機能

#### 💬 チャット履歴
- **詳細表示**: 選択したセッションの会話を時系列表示
- **リアルタイム更新**: 実行中セッションの自動更新
- **表示クリア**: 🧹ボタンで表示をクリア

#### 🛠️ グローバル操作（サイドバー）
- **🧹 全画面クリア**: 現在の画面表示を完全にクリア
- **🔄 システム再起動**: アプリケーション状態を完全にリセット

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

- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI エンドポイント
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API キー
- `AOAI_DEPLOYMENT_CHAT`: Azure OpenAI チャット用デプロイメント名
- `AOAI_DEPLOYMENT_REASONING`: Azure OpenAI 推論用デプロイメント名
- `AZURE_API_VERSION`: Azure OpenAI API バージョン（デフォルト: 2025-04-01-preview）
- `COSMOSDB_ENABLED`: CosmosDB使用フラグ（デフォルト: false）
- `COSMOSDB_ENDPOINT`: CosmosDB エンドポイント（オプション）
- `COSMOSDB_KEY`: CosmosDB アクセスキー（オプション）
- `COSMOSDB_DATABASE_NAME`: CosmosDB データベース名（デフォルト: ai_brainstorming）
- `COSMOSDB_CONTAINER_NAME`: CosmosDB コンテナー名（デフォルト: chat_sessions）

### 設定ファイル

- `.env`: 環境変数設定ファイル
- `.env.example`: 環境変数設定のテンプレート

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

### SelectorGroupChat による協調動作
- **Selector Agent**: 司会役として次に発言するエージェントを動的に選択
- **終了条件**: 各エージェントが規定回数発言した時点で自動終了
- **議論の流れ**: 自然な会話の流れを重視した進行管理

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

## 🛠️ 今後の拡張計画

### Azure Functions化
- [ ] **AutoGen API化**: AutoGenセッションをAzure Functionsで実行
- [ ] **Queue Trigger実装**: Azure Service Bus QueueまたはAzure Storage Queueでの非同期処理
- [ ] **RESTful API**: セッション作成・管理のためのREST API
- [ ] **認証・認可**: Azure AD認証とAPIキー管理

### ViewツールのQueue対応
- [ ] **Queue登録機能**: StreamlitからQueue経由でセッション開始
- [ ] **非同期監視**: Queue状態とセッション進行状況の監視
- [ ] **WebHook対応**: セッション完了通知の受信
- [ ] **リアルタイム通信**: SignalRによるライブ更新

### ViewツールのNextjs化
- [ ] **Next.jsフロントエンド**: Reactベースのフロントエンド開発
- [ ] **API連携**: Azure QueueとCosmosDBとの連携
- [ ] **状態管理**: ReduxまたはContext APIによる状態管理
- [ ] **SSR対応**: Next.jsのサーバーサイドレンダリング機能を活用
- [ ] **UIコンポーネントライブラリ**: Material-UIやTailwind CSSを使用したスタイリング

## ライセンス

MIT License
