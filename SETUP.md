# 🚀 AI Brainstorming System セットアップガイド

このドキュメントでは、AI Brainstorming Systemを初回セットアップから実行まで詳細に説明します。

## 📋 前提条件

### システム要件
- **Python**: 3.11以上
- **OS**: Windows 10/11, macOS, Linux
- **メモリ**: 最低 4GB RAM
- **ストレージ**: 最低 1GB の空き容量

### 必要なアカウント・サービス

1. **Azure OpenAI** または **OpenAI** アカウント
   - GPT-4 モデルへのアクセス権限
   - API キーの取得

2. **Azure CosmosDB** (オプション)
   - リアルタイムデータ保存を使用する場合
   - Core (SQL) API タイプのアカウント

## 🔧 ステップ1: リポジトリのセットアップ

### 1.1 リポジトリのクローン

```bash
# HTTPSでクローン
git clone https://github.com/your-username/ai-brainstorming-system.git

# SSHでクローン（推奨）
git clone git@github.com:your-username/ai-brainstorming-system.git

# ディレクトリに移動
cd ai-brainstorming-system
```

### 1.2 仮想環境の作成

#### Windows
```cmd
# Python仮想環境を作成
python -m venv .venv

# 仮想環境をアクティベート
.venv\Scripts\activate

# アクティベート確認
where python
# 出力: C:\path\to\ai-brainstorming-system\.venv\Scripts\python.exe
```

#### macOS/Linux
```bash
# Python仮想環境を作成
python3 -m venv .venv

# 仮想環境をアクティベート
source .venv/bin/activate

# アクティベート確認
which python
# 出力: /path/to/ai-brainstorming-system/.venv/bin/python
```

### 1.3 依存関係のインストール

```bash
# メイン依存関係をインストール
pip install -r requirements.txt

# 開発用依存関係も使用する場合
pip install -r requirements-dev.txt

# インストール確認
pip list | grep -E "(autogen|streamlit|azure-cosmos)"
```

## ⚙️ ステップ2: 環境変数の設定

### 2.1 環境変数ファイルの作成

```bash
# .env.example をコピー
cp .env.example .env

# エディタで開く（例: VS Code）
code .env
```

### 2.2 Azure OpenAI の設定

Azure ポータルで以下の情報を取得：

1. **エンドポイント**: `https://your-resource.openai.azure.com/`
2. **APIキー**: リソースの「キーとエンドポイント」から取得
3. **デプロイメント名**: モデルのデプロイメント名

```bash
# .env ファイルに設定
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_actual_api_key_here
AOAI_DEPLOYMENT_CHAT=gpt-4
AOAI_DEPLOYMENT_REASONING=gpt-4
```

### 2.3 OpenAI の設定（代替）

Azure OpenAI の代わりに OpenAI を使用する場合：

```bash
# Azure OpenAI の設定をコメントアウトし、以下を設定
# AZURE_OPENAI_ENDPOINT=...
# AZURE_OPENAI_API_KEY=...

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
```

### 2.4 CosmosDB の設定（オプション）

リアルタイムデータ保存を使用する場合：

```bash
COSMOSDB_ENABLED=true
COSMOSDB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOSDB_KEY=your_primary_key_here
COSMOSDB_DATABASE_NAME=ai_brainstorming
COSMOSDB_CONTAINER_NAME=chat_sessions
```

## 🧪 ステップ3: 動作確認

### 3.1 基本動作テスト

```bash
# ヘルスチェック実行
python src/main.py --health-check

# 期待される出力:
# ✅ Azure OpenAI connection OK
# ✅ Configuration loaded successfully
# ✅ All systems operational
```

### 3.2 CosmosDB 接続テスト（該当する場合）

```bash
# CosmosDB接続テスト
python scripts/quick_cosmosdb_test.py

# 期待される出力:
# ✓ azure-cosmos available
# ✓ aiohttp available
# ✓ Connected successfully
# 🎉 CosmosDB connection successful!
```

### 3.3 簡単なブレインストーミング実行

```bash
# 簡単なテストタスク実行
python src/main.py --task "新しいスマートフォンアプリのアイデア検討"

# エージェントの会話が始まることを確認
```

## 📊 ステップ4: Streamlit ダッシュボードのセットアップ

### 4.1 Streamlit 起動

```bash
# Streamlit ダッシュボード起動
python scripts/run_streamlit.py

# または簡単起動
run_chat_viewer.bat  # Windows
./run_chat_viewer.sh  # macOS/Linux
```

### 4.2 ダッシュボードアクセス

1. ブラウザで `http://localhost:8501` にアクセス
2. サイドバーで CosmosDB 接続状態を確認
3. セッション一覧が表示されることを確認

## 🎯 ステップ5: 実際の使用

### 5.1 ブレインストーミング実行

```bash
# インタラクティブモード
python src/main.py

# プロンプトが表示されたらタスクを入力
# 例: "新しいフィットネスアプリの企画検討"
```

### 5.2 リアルタイム監視

別のターミナルで：
```bash
# Streamlit ダッシュボードを起動
python scripts/run_streamlit.py

# ブラウザで進行状況をリアルタイム監視
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. Python バージョンエラー
```bash
# Python バージョン確認
python --version

# Python 3.11+ でない場合はアップデート
# Windows: https://www.python.org/downloads/
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
```

#### 2. モジュール不足エラー
```bash
# 仮想環境がアクティベートされているか確認
which python  # macOS/Linux
where python   # Windows

# 依存関係を再インストール
pip install -r requirements.txt --force-reinstall
```

#### 3. Azure OpenAI 接続エラー
```bash
# エンドポイントURL確認
curl -H "api-key: YOUR_API_KEY" \
  "https://your-resource.openai.azure.com/openai/deployments?api-version=2023-05-15"

# .env ファイルの設定確認
cat .env | grep AZURE_OPENAI
```

#### 4. CosmosDB 接続エラー
```bash
# 接続テスト実行
python scripts/test_cosmosdb_connection.py

# 設定確認
python scripts/quick_cosmosdb_test.py
```

#### 5. Streamlit 起動エラー
```bash
# ポート使用状況確認
netstat -an | grep 8501

# 別のポートで起動
streamlit run src/web/streamlit_app.py --server.port 8502
```

### ログ確認

```bash
# アプリケーションログ確認
cat logs/app_$(date +%Y%m%d).log

# 最新ログをリアルタイム監視
tail -f logs/app_$(date +%Y%m%d).log
```

## 📚 次のステップ

### 基本使用法
1. [README.md](README.md) - 基本的な使い方
2. [CosmosDB設定](docs/CosmosDB_Setup.md) - データベース詳細設定
3. [Streamlit使用法](docs/Streamlit_Chat_Viewer.md) - ダッシュボード活用法

### カスタマイズ
1. エージェント設定の調整: `src/agents/`
2. プロンプトのカスタマイズ: `src/config/prompts.py`
3. UI テーマの変更: `src/web/streamlit_app.py`

### 開発参加
1. [CONTRIBUTING.md](CONTRIBUTING.md) - 開発ガイドライン
2. Issues & Pull Requests への参加

## 💬 サポート

### 質問・相談
- **GitHub Issues**: バグ報告・機能要望
- **GitHub Discussions**: 使用方法の質問・アイデア交換
- **Email**: project-email@example.com

### 有用なリンク
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Azure CosmosDB Documentation](https://docs.microsoft.com/azure/cosmos-db/)

---

🎉 **セットアップ完了！** AI Brainstorming System をお楽しみください！