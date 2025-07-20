# Streamlit Chat Viewer - 使い方ガイド

## 概要

AI Brainstorming Systemのチャット履歴をリアルタイムで確認できるWebアプリケーションです。CosmosDBに保存されたセッションデータとメッセージを視覚的に表示します。

## 機能

### 📋 セッション一覧画面
- 過去のブレインストーミングセッション一覧を表示
- ステータス（実行中/完了/失敗）をアイコンで表示
- タスク内容、実行時間、メッセージ数などの情報
- セッション選択してチャット詳細に移動

### 💬 チャット表示画面
- 選択したセッションのチャット履歴を時系列で表示
- エージェント別にアバターとカラーで区別
- **リアルタイム更新**: 実行中セッションでは自動ポーリング
- セッション詳細情報（実行時間、エージェント数など）

## 起動方法

### 前提条件: .venv環境の準備
```bash
# 仮想環境作成（初回のみ）
python -m venv .venv

# 仮想環境アクティベート
.venv\Scripts\activate  # Windows
# または
source .venv/bin/activate  # Linux/Mac

# 依存関係インストール
pip install -r requirements.txt
```

### 方法1: バッチファイルで起動（簡単）
```bash
# Windows
run_chat_viewer.bat

# Linux/Mac
./run_chat_viewer.sh
```

### 方法2: Pythonスクリプトで起動
```bash
# .venv環境のPythonで実行
.venv\Scripts\python.exe scripts/run_streamlit.py  # Windows
# または
.venv/bin/python scripts/run_streamlit.py  # Linux/Mac
```

### 方法3: 仮想環境をアクティベートして起動
```bash
.venv\Scripts\activate  # Windows
streamlit run src/web/streamlit_app.py
```

## アクセス
ブラウザで以下のURLにアクセス：
```
http://localhost:8501
```

## 必要な設定

### 1. 仮想環境と依存関係のセットアップ
```bash
# 仮想環境作成
python -m venv .venv

# 仮想環境アクティベート
.venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. CosmosDB設定
`.env`ファイルで以下を設定：
```bash
COSMOSDB_ENABLED=true
COSMOSDB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOSDB_KEY=your-primary-key
COSMOSDB_DATABASE_NAME=ai_brainstorming
COSMOSDB_CONTAINER_NAME=chat_sessions
```

## 画面構成

### サイドバー
- **🎛️ ナビゲーション**: ページ切り替え
- **接続状態**: CosmosDB接続ステータス表示
- **バージョン情報**: アプリケーション情報

### メイン画面

#### セッション一覧
| 項目 | 説明 |
|------|------|
| セッションID | 一意のセッション識別子 |
| ステータス | 🟡実行中 / 🟢完了 / 🔴失敗 |
| タスク | ブレインストーミングのテーマ |
| 開始時刻 | セッション開始日時 |
| 実行時間 | セッション継続時間 |
| メッセージ数 | エージェント発言回数 |
| 最終更新 | 最後にデータが更新された時刻 |

#### チャット表示
- **エージェント識別**: 各AIエージェントを色とアイコンで区別
  - 🎨 クリエイティブプランナー
  - 📊 マーケットアナリスト
  - ⚙️ テクニカルバリデーター
  - 💼 ビジネスエバリュエーター
  - 👥 ユーザーアドボケート

- **タイムスタンプ**: 各メッセージの発言時刻
- **リアルタイム更新**: 実行中セッションで新しいメッセージを自動取得

## リアルタイム機能

### 自動更新の仕組み
1. **実行中セッション検出**: ステータスが「running」のセッション
2. **ポーリング間隔**: 3秒ごとにCosmosDBをチェック
3. **メッセージ数監視**: 新しいメッセージが追加されると画面更新
4. **完了検出**: セッションが完了すると自動更新を停止

### 手動更新
- 🔄 更新ボタンでいつでも最新データを取得
- セッション一覧、チャット画面両方で利用可能

## トラブルシューティング

### CosmosDB接続エラー
- サイドバーで接続状態を確認
- `.env`ファイルの設定値をチェック
- ネットワーク接続とCosmosDBサービス状態を確認

### データが表示されない
- CosmosDBにセッションデータが存在するか確認
- パーティションキー設定が正しいかチェック
- ログでエラーメッセージを確認

### パフォーマンス問題
- セッション数が多い場合は表示件数制限（デフォルト50件）
- 自動更新間隔の調整（現在3秒）
- CosmosDBのRequest Unitsを確認

## カスタマイズ

### エージェントアバターの変更
`streamlit_app.py`の`agent_avatars`辞書を編集：
```python
agent_avatars = {
    'creative_planner': '🎨',
    'market_analyst': '📊',
    # 新しいエージェントを追加
    'new_agent': '🚀'
}
```

### ポーリング間隔の変更
`show_chat_page`関数の`time.sleep(3)`を調整

### 表示件数の変更
`get_sessions(limit=50)`のlimit値を変更

## API リファレンス

### CosmosDBReader クラス
| メソッド | 説明 |
|----------|------|
| `get_sessions(limit)` | セッション一覧取得 |
| `get_session_messages(session_id)` | セッションメッセージ取得 |
| `get_session_detail(session_id)` | セッション詳細取得 |
| `check_session_status(session_id)` | セッションステータス確認 |
| `is_available()` | CosmosDB接続状態確認 |

### セッションデータ構造
```python
{
    'id': 'session_20250717_210000_12345',
    'status': 'running|completed|failed',
    'task': 'ブレインストーミングのテーマ',
    'start_time': '2025-07-17 21:00:00.000',
    'statistics': {
        'total_messages': 15,
        'agent_message_counts': {...}
    }
}
```

## 今後の拡張予定

- 📊 セッション分析ダッシュボード
- 🔍 メッセージ検索機能
- 📤 チャット履歴エクスポート
- 🎨 テーマカスタマイズ
- 📱 レスポンシブデザイン対応