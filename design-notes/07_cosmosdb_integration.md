# データ永続化とCosmosDB連携

AIエージェントの議論をリアルタイムで保存し、後から検索・分析できるデータ永続化システムの実装について詳しく解説します。

## なぜCosmosDBを選んだのか

### 要件分析

このシステムには以下のデータストア要件がありました：

1. **リアルタイム書き込み**: エージェントの発言を即座に保存
2. **柔軟なスキーマ**: メッセージ形式の変更に対応
3. **高速読み取り**: 過去のセッション検索とチャット履歴表示
4. **スケーラビリティ**: 将来的な大量データ対応

### 技術選択の比較

| データストア | 長所 | 短所 | 採用理由 |
|-------------|------|------|----------|
| PostgreSQL | ACID保証、SQL | スキーマ固定 | × |
| MongoDB | JSONネイティブ | 運用負荷 | △ |
| CosmosDB | グローバル分散、低遅延 | コスト | ◯ |
| Firestore | リアルタイム同期 | ベンダーロック | △ |

CosmosDBの「グローバル分散」「ミリ秒単位の遅延」「JSONネイティブ」という特徴が要件にマッチしました。

## パーティションキー設計

### 設計検討プロセス

CosmosDBで最も重要なのがパーティションキーの設計です。以下の要素を考慮しました：

```
データアクセスパターン分析：
1. セッション単位でのメッセージ取得（最頻繁）
2. 全セッション一覧の取得（頻繁）
3. 特定期間のセッション検索（時々）
4. エージェント別の発言分析（稀）
```

### 最終的なパーティションキー設計

```json
{
  "パーティションキー": "/session_id",
  "理由": [
    "セッション単位でのデータ取得が最も頻繁",
    "セッション内のメッセージは時系列で関連性が高い",
    "1セッションのデータサイズは適切（数MB程度）",
    "ホットパーティション問題を回避可能"
  ]
}
```

### データ構造設計

```python
# セッション情報ドキュメント
session_document = {
    "id": "session_20240120_143022",
    "session_id": "session_20240120_143022",  # パーティションキー
    "type": "session_info",
    "task": "リモートワーク時代の新しいコミュニケーションツール",
    "created_at": "2024-01-20T14:30:22.123456",
    "status": "completed",
    "message_count": 15,
    "participants": ["creative_planner", "market_analyst", "technical_validator", "business_evaluator", "user_advocate"]
}

# メッセージドキュメント
message_document = {
    "id": "session_20240120_143022_msg_0001_1705737022123456",
    "session_id": "session_20240120_143022",  # パーティションキー
    "type": "message",
    "source": "creative_planner",
    "content": "物理的な距離を感じさせない『空間共有型』のツールを提案します...",
    "timestamp": "2024-01-20T14:30:25.123456",
    "sequence": 1
}
```

## CosmosDBManagerの実装

### 基本クラス構造

```python
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
import asyncio
import time
from typing import Dict, List, Any, Optional

class CosmosDBManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        self.database = None
        self.container = None
        self.session_id = None
        
    async def initialize(self, session_id: str):
        """CosmosDB接続を初期化"""
        try:
            self.session_id = session_id
            
            # 非同期クライアントを作成
            self.client = CosmosClient(
                url=self.settings.cosmosdb_endpoint,
                credential=self.settings.cosmosdb_key
            )
            
            # データベースとコンテナーを取得（存在しない場合は作成）
            self.database = await self._get_or_create_database()
            self.container = await self._get_or_create_container()
            
            safe_print(f"CosmosDB初期化完了: {session_id}")
            
        except Exception as e:
            safe_print(f"CosmosDB初期化エラー: {e}")
            raise
```

### データベース・コンテナー初期化

```python
async def _get_or_create_database(self):
    """データベースを取得または作成"""
    database_name = self.settings.cosmosdb_database_name
    
    try:
        database = await self.client.create_database_if_not_exists(
            id=database_name
        )
        return database
    except Exception as e:
        safe_print(f"データベース作成エラー: {e}")
        raise

async def _get_or_create_container(self):
    """コンテナーを取得または作成"""
    container_name = self.settings.cosmosdb_container_name
    
    try:
        container = await self.database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/session_id"),
            offer_throughput=400  # 最小スループット（コスト最適化）
        )
        return container
    except Exception as e:
        safe_print(f"コンテナー作成エラー: {e}")
        raise
```

## リアルタイム保存の実装

### メッセージ保存機能

```python
async def save_message_realtime(self, message_data: Dict[str, Any], max_retries: int = 3):
    """メッセージをリアルタイムで保存（リトライ機能付き）"""
    
    for attempt in range(max_retries):
        try:
            # 既存メッセージ数を取得してシーケンス番号を決定
            current_messages = await self.get_session_messages()
            sequence = len(current_messages) + 1
            
            # ユニークIDを生成（マイクロ秒まで含めて重複回避）
            unique_id = f"{self.session_id}_msg_{sequence:04d}_{int(time.time() * 1000000)}"
            
            # ドキュメント構造を作成
            message_doc = {
                "id": unique_id,
                "session_id": self.session_id,
                "type": "message",
                "source": message_data["source"],
                "content": message_data["content"],
                "timestamp": message_data["timestamp"],
                "sequence": sequence
            }
            
            # CosmosDBに非同期保存
            await self.container.create_item(message_doc)
            
            safe_print(f"メッセージ保存成功: {unique_id}")
            return unique_id
            
        except Exception as e:
            if attempt == max_retries - 1:  # 最後の試行
                safe_print(f"メッセージ保存エラー（最終試行）: {e}")
                raise
            else:
                safe_print(f"メッセージ保存エラー（試行{attempt + 1}/{max_retries}）: {e}")
                await asyncio.sleep(2 ** attempt)  # 指数バックオフ
```

### セッション情報の管理

```python
async def save_session_info(self, task: str, status: str = "active"):
    """セッション情報を保存"""
    try:
        session_doc = {
            "id": self.session_id,
            "session_id": self.session_id,
            "type": "session_info",
            "task": task,
            "created_at": datetime.now().isoformat(),
            "status": status,
            "message_count": 0,
            "participants": [
                "creative_planner",
                "market_analyst", 
                "technical_validator",
                "business_evaluator",
                "user_advocate"
            ]
        }
        
        await self.container.create_item(session_doc)
        safe_print(f"セッション情報保存: {self.session_id}")
        
    except Exception as e:
        safe_print(f"セッション情報保存エラー: {e}")
        raise

async def update_session_status(self, status: str, message_count: int = None):
    """セッションステータスを更新"""
    try:
        # 既存のセッション情報を取得
        session_doc = await self.container.read_item(
            item=self.session_id,
            partition_key=self.session_id
        )
        
        # ステータスを更新
        session_doc["status"] = status
        session_doc["updated_at"] = datetime.now().isoformat()
        
        if message_count is not None:
            session_doc["message_count"] = message_count
        
        # 更新を保存
        await self.container.replace_item(
            item=session_doc,
            body=session_doc
        )
        
    except Exception as e:
        safe_print(f"セッションステータス更新エラー: {e}")
```

## データ取得とクエリ最適化

### セッションメッセージの取得

```python
async def get_session_messages(self) -> List[Dict[str, Any]]:
    """セッションの全メッセージを時系列順で取得"""
    try:
        # パーティションキーを指定したクエリ（効率的）
        query = """
            SELECT * FROM c 
            WHERE c.session_id = @session_id 
            AND c.type = 'message' 
            ORDER BY c.sequence ASC
        """
        
        parameters = [{"name": "@session_id", "value": self.session_id}]
        
        # クエリ実行
        items = []
        async for item in self.container.query_items(
            query=query,
            parameters=parameters,
            partition_key=self.session_id  # パーティション内クエリ
        ):
            items.append(item)
        
        return items
        
    except Exception as e:
        safe_print(f"メッセージ取得エラー: {e}")
        return []
```

### 全セッション一覧の取得

```python
async def get_all_sessions(self) -> List[Dict[str, Any]]:
    """全セッション一覧を取得（新しい順）"""
    try:
        # クロスパーティションクエリ（必要な場合のみ）
        query = """
            SELECT * FROM c 
            WHERE c.type = 'session_info' 
            ORDER BY c.created_at DESC
        """
        
        items = []
        async for item in self.container.query_items(
            query=query,
            enable_cross_partition_query=True  # 複数パーティション検索
        ):
            items.append(item)
        
        return items
        
    except Exception as e:
        safe_print(f"セッション一覧取得エラー: {e}")
        return []
```

## パフォーマンス最適化

### 接続プーリングと再利用

```python
class CosmosDBConnectionPool:
    """CosmosDB接続プールの管理"""
    
    _instance = None
    _client = None
    
    def __new__(cls, settings: Settings):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_client(self) -> CosmosClient:
        """再利用可能なクライアントを取得"""
        if self._client is None:
            self._client = CosmosClient(
                url=self.settings.cosmosdb_endpoint,
                credential=self.settings.cosmosdb_key,
                consistency_level="Session"  # パフォーマンス重視
            )
        return self._client
    
    async def close(self):
        """接続を閉じる"""
        if self._client:
            await self._client.close()
            self._client = None
```

### バッチ処理による効率化

```python
async def save_messages_batch(self, messages: List[Dict[str, Any]]):
    """複数メッセージの一括保存"""
    try:
        # バッチ操作を準備
        batch_operations = []
        
        for i, message_data in enumerate(messages):
            unique_id = f"{self.session_id}_msg_{i+1:04d}_{int(time.time() * 1000000)}"
            
            message_doc = {
                "id": unique_id,
                "session_id": self.session_id,
                "type": "message",
                "source": message_data["source"],
                "content": message_data["content"],
                "timestamp": message_data["timestamp"],
                "sequence": i + 1
            }
            
            batch_operations.append(("create", message_doc))
        
        # バッチ実行（同一パーティション内）
        await self.container.execute_item_batch(
            batch_operations,
            partition_key=self.session_id
        )
        
        safe_print(f"バッチ保存完了: {len(messages)}件")
        
    except Exception as e:
        safe_print(f"バッチ保存エラー: {e}")
        # フォールバック: 個別保存
        for message in messages:
            await self.save_message_realtime(message)
```

## コスト最適化と監視

### スループット管理

```python
async def optimize_throughput(self):
    """使用状況に応じてスループットを調整"""
    try:
        container_info = await self.container.read()
        current_throughput = container_info.get("throughput", 400)
        
        # 使用状況を確認
        recent_sessions = await self.get_recent_sessions(hours=1)
        
        if len(recent_sessions) > 10:  # 高負荷時
            new_throughput = min(current_throughput * 2, 4000)
        elif len(recent_sessions) == 0:  # 低負荷時
            new_throughput = max(current_throughput // 2, 400)
        else:
            return  # 変更不要
        
        # スループットを更新
        await self.container.replace_throughput(new_throughput)
        safe_print(f"スループット調整: {current_throughput} → {new_throughput}")
        
    except Exception as e:
        safe_print(f"スループット調整エラー: {e}")
```

### 使用量監視

```python
async def get_usage_metrics(self) -> Dict[str, Any]:
    """使用量メトリクスを取得"""
    try:
        # 最近30日のメトリクス
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        query = """
            SELECT 
                COUNT(1) as total_sessions,
                SUM(c.message_count) as total_messages,
                AVG(c.message_count) as avg_messages_per_session
            FROM c 
            WHERE c.type = 'session_info' 
            AND c.created_at >= @start_date
        """
        
        parameters = [{"name": "@start_date", "value": thirty_days_ago.isoformat()}]
        
        result = []
        async for item in self.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ):
            result.append(item)
        
        return result[0] if result else {}
        
    except Exception as e:
        safe_print(f"使用量取得エラー: {e}")
        return {}
```

この実装により、スケーラブルで効率的なデータ永続化システムを実現しています。次のセクションでは、開発過程で遭遇した技術的課題とその解決方法について詳しく解説します。