"""
CosmosDB Setup Script - データベースとコンテナの初期設定
"""

import os
import sys
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 環境変数を読み込み
load_dotenv()

def setup_cosmosdb():
    """CosmosDBのデータベースとコンテナを作成する"""
    
    # 設定値を取得
    endpoint = os.getenv('COSMOSDB_ENDPOINT')
    key = os.getenv('COSMOSDB_KEY')
    database_name = os.getenv('COSMOSDB_DATABASE_NAME', 'ai_brainstorming')
    container_name = os.getenv('COSMOSDB_CONTAINER_NAME', 'chat_sessions')
    
    if not endpoint or not key:
        print("ERROR: COSMOSDB_ENDPOINT and COSMOSDB_KEY must be set in environment variables")
        return False
    
    try:
        # CosmosDBクライアントを作成
        client = CosmosClient(endpoint, key)
        print(f"Connected to CosmosDB: {endpoint}")
        
        # データベースを作成（存在しない場合）
        try:
            database = client.create_database(
                id=database_name,
                offer_throughput=400  # 共有RU
            )
            print(f"Created database: {database_name}")
        except exceptions.CosmosResourceExistsError:
            database = client.get_database_client(database_name)
            print(f"Database already exists: {database_name}")
        
        # コンテナを作成（存在しない場合）
        try:
            container = database.create_container(
                id=container_name,
                partition_key=PartitionKey(path="/session_id"),
                offer_throughput=400  # 専用RU
            )
            print(f"Created container: {container_name} with partition key /session_id")
        except exceptions.CosmosResourceExistsError:
            container = database.get_container_client(container_name)
            print(f"Container already exists: {container_name}")
        
        # インデックスポリシーを設定
        indexing_policy = {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {
                    "path": "/*"
                }
            ],
            "excludedPaths": [
                {
                    "path": "/content/*"  # メッセージ内容はインデックス除外
                }
            ]
        }
        
        # コンテナの設定を更新
        try:
            container.replace_container(
                partition_key=PartitionKey(path="/session_id"),
                indexing_policy=indexing_policy
            )
            print("Updated container indexing policy")
        except Exception as e:
            print(f"Warning: Could not update indexing policy: {e}")
        
        # テストドキュメントを作成
        test_doc = {
            "id": "test_setup",
            "session_id": "test_setup",
            "type": "test",
            "message": "CosmosDB setup test document",
            "ttl": 60  # 60秒後に自動削除
        }
        
        try:
            container.create_item(test_doc)
            print("Test document created successfully")
            
            # テストドキュメントを読み取り
            read_doc = container.read_item(
                item="test_setup",
                partition_key="test_setup"
            )
            print("Test document read successfully")
            
        except Exception as e:
            print(f"Warning: Test document operation failed: {e}")
        
        print("\n=== CosmosDB Setup Complete ===")
        print(f"Database: {database_name}")
        print(f"Container: {container_name}")
        print(f"Partition Key: /session_id")
        print(f"Throughput: 400 RU/s")
        print("\nYou can now set COSMOSDB_ENABLED=true in your .env file")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to setup CosmosDB: {e}")
        return False

def verify_setup():
    """セットアップの検証"""
    endpoint = os.getenv('COSMOSDB_ENDPOINT')
    key = os.getenv('COSMOSDB_KEY')
    database_name = os.getenv('COSMOSDB_DATABASE_NAME', 'ai_brainstorming')
    container_name = os.getenv('COSMOSDB_CONTAINER_NAME', 'chat_sessions')
    
    if not endpoint or not key:
        print("ERROR: CosmosDB credentials not found in environment variables")
        return False
    
    try:
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        # 簡単なクエリでテスト
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'test'"
        result = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        print("✓ CosmosDB connection verified")
        print(f"✓ Database '{database_name}' accessible")
        print(f"✓ Container '{container_name}' accessible")
        print(f"✓ Query execution successful")
        
        return True
        
    except Exception as e:
        print(f"✗ CosmosDB verification failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CosmosDB Setup Tool")
    parser.add_argument("--verify", action="store_true", help="Verify existing setup")
    args = parser.parse_args()
    
    if args.verify:
        success = verify_setup()
    else:
        success = setup_cosmosdb()
    
    sys.exit(0 if success else 1)