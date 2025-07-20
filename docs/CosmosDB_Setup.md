# CosmosDB連携設定

## 概要

AI Brainstorming Systemでは、エージェントが回答するたびにリアルタイムでチャット履歴をCosmosDBに保存できます。

## CosmosDBの準備

### 1. CosmosDBアカウントの作成

1. Azure PortalでCosmosDBアカウントを作成
2. API種別として **Core (SQL)** を選択
3. データベース名: `ai_brainstorming`
4. コンテナ名: `chat_sessions`
5. パーティションキー: `/session_id`

### 2. データベースとコンテナの作成

#### 自動セットアップ（推奨）
```bash
# CosmosDBの自動セットアップ
python scripts/setup_cosmosdb.py

# セットアップの確認
python scripts/setup_cosmosdb.py --verify
```

#### 手動セットアップ
Azure Portalで以下を作成：

- **データベース名**: `ai_brainstorming`
- **コンテナ名**: `chat_sessions`
- **パーティションキー**: `/session_id`
- **Throughput**: 400 RU/s
- **インデックスポリシー**: コンテンツフィールド除外

## 設定方法

### 1. 環境変数の設定

`.env`ファイルに以下を追加：

```bash
# CosmosDB設定
COSMOSDB_ENABLED=true
COSMOSDB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOSDB_KEY=your-primary-key
COSMOSDB_DATABASE_NAME=ai_brainstorming
COSMOSDB_CONTAINER_NAME=chat_sessions
```

### 2. 設定値の説明

- **COSMOSDB_ENABLED**: CosmosDB連携の有効/無効
- **COSMOSDB_ENDPOINT**: CosmosDBアカウントのエンドポイント
- **COSMOSDB_KEY**: プライマリキーまたはセカンダリキー
- **COSMOSDB_DATABASE_NAME**: データベース名
- **COSMOSDB_CONTAINER_NAME**: コンテナ名

## データ構造

### セッションドキュメント

```json
{
  "id": "session_20250717_210000_12345",
  "type": "session",
  "task": "新しいモバイルアプリサービスの企画を検討します...",
  "start_time": "2025-07-17 21:00:00.000",
  "end_time": "2025-07-17 21:15:30.500",
  "status": "completed",
  "execution_time": 930.5,
  "team_info": {
    "agent_count": 6,
    "agent_names": ["creative_planner", "market_analyst", ...]
  },
  "statistics": {
    "total_messages": 15,
    "agent_message_counts": {
      "creative_planner": 3,
      "market_analyst": 4,
      "technical_validator": 3,
      "business_evaluator": 3,
      "user_advocate": 2
    }
  },
  "created_at": "2025-07-17 21:00:00.000",
  "updated_at": "2025-07-17 21:15:30.500"
}
```

### メッセージドキュメント

```json
{
  "id": "session_20250717_210000_12345_msg_1",
  "type": "message",
  "session_id": "session_20250717_210000_12345",
  "source": "creative_planner",
  "content": "もし「感情や気分」を可視化できるアプリがあれば...",
  "message_type": "TextMessage",
  "timestamp": "2025-07-17 21:00:15.123",
  "created_at": "2025-07-17 21:00:15.123"
}
```

## 利用方法

### 1. リアルタイム保存

CosmosDBが有効な場合、以下のタイミングで自動保存されます：

- **セッション開始時**: セッションドキュメント作成
- **エージェント回答時**: メッセージドキュメント作成とセッション統計更新
- **セッション終了時**: セッションドキュメント完了状態に更新

### 2. 無効化

CosmosDBを使用しない場合：

```bash
COSMOSDB_ENABLED=false
```

この場合、従来通りローカルJSONファイルのみに保存されます。

## クエリ例

### 最新セッション取得

```sql
SELECT * FROM c 
WHERE c.type = 'session' 
ORDER BY c.created_at DESC 
OFFSET 0 LIMIT 10
```

### 特定セッションのメッセージ取得

```sql
SELECT * FROM c 
WHERE c.type = 'message' 
AND c.session_id = 'session_20250717_210000_12345'
ORDER BY c.timestamp
```

### エージェント別メッセージ数

```sql
SELECT c.source, COUNT(1) as message_count
FROM c 
WHERE c.type = 'message'
GROUP BY c.source
```

## トラブルシューティング

### 接続エラー

1. エンドポイントURLが正しいか確認
2. キーが有効か確認
3. データベース・コンテナが存在するか確認

### 権限エラー

CosmosDBキーに以下の権限が必要：
- 読み取り権限
- 書き込み権限

### パフォーマンス

大量メッセージがある場合：
- Request Units (RU)の調整を検討
- インデックスポリシーの最適化

## 監視

### ログ確認

```bash
# CosmosDB関連ログの確認
grep "CosmosDB" logs/app_*.log
```

### ヘルスチェック

```bash
python main.py --health-check
```

CosmosDB接続状態も確認されます。