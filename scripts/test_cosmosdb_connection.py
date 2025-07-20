"""
CosmosDB Connection Test - CosmosDBとの接続テスト
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_import():
    """必要なライブラリのインポートテスト"""
    print("=== Import Test ===")
    
    try:
        from azure.cosmos import CosmosClient, exceptions
        print("✓ azure.cosmos imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import azure.cosmos: {e}")
        return False
    
    try:
        from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
        print("✓ azure.cosmos.aio imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import azure.cosmos.aio: {e}")
        return False
    
    try:
        import aiohttp
        print("✓ aiohttp imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import aiohttp: {e}")
        return False
    
    return True

def test_environment():
    """環境変数のテスト"""
    print("\n=== Environment Variables Test ===")
    
    load_dotenv()
    
    required_vars = [
        'COSMOSDB_ENDPOINT',
        'COSMOSDB_KEY',
        'COSMOSDB_DATABASE_NAME',
        'COSMOSDB_CONTAINER_NAME'
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # キーは一部のみ表示
            if 'KEY' in var and len(value) > 10:
                display_value = f"{value[:8]}...{value[-4:]}"
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
        else:
            print(f"✗ {var}: Not set")
            all_present = False
    
    enabled = os.getenv('COSMOSDB_ENABLED', 'false').lower() == 'true'
    print(f"{'✓' if enabled else '○'} COSMOSDB_ENABLED: {enabled}")
    
    return all_present

def test_sync_connection():
    """同期接続のテスト"""
    print("\n=== Synchronous Connection Test ===")
    
    try:
        from azure.cosmos import CosmosClient, exceptions
        
        endpoint = os.getenv('COSMOSDB_ENDPOINT')
        key = os.getenv('COSMOSDB_KEY')
        database_name = os.getenv('COSMOSDB_DATABASE_NAME', 'ai_brainstorming')
        container_name = os.getenv('COSMOSDB_CONTAINER_NAME', 'chat_sessions')
        
        if not endpoint or not key:
            print("✗ CosmosDB credentials not available")
            return False
        
        # クライアント作成
        client = CosmosClient(endpoint, key)
        print("✓ CosmosClient created successfully")
        
        # データベース接続テスト
        try:
            database = client.get_database_client(database_name)
            # データベース情報を取得してテスト
            db_info = database.read()
            print(f"✓ Database '{database_name}' accessible")
        except exceptions.CosmosResourceNotFoundError:
            print(f"✗ Database '{database_name}' not found")
            return False
        except Exception as e:
            print(f"✗ Database access failed: {e}")
            return False
        
        # コンテナ接続テスト
        try:
            container = database.get_container_client(container_name)
            # コンテナ情報を取得してテスト
            container_info = container.read()
            print(f"✓ Container '{container_name}' accessible")
            print(f"  Partition key: {container_info.get('partitionKey', {}).get('paths', ['Not found'])}")
        except exceptions.CosmosResourceNotFoundError:
            print(f"✗ Container '{container_name}' not found")
            return False
        except Exception as e:
            print(f"✗ Container access failed: {e}")
            return False
        
        # 簡単なクエリテスト
        try:
            query = "SELECT VALUE COUNT(1) FROM c"
            result = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            count = result[0] if result else 0
            print(f"✓ Query test successful - Document count: {count}")
        except Exception as e:
            print(f"✗ Query test failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Sync connection test failed: {e}")
        return False

async def test_async_connection():
    """非同期接続のテスト"""
    print("\n=== Asynchronous Connection Test ===")
    
    try:
        from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
        from azure.cosmos import exceptions
        
        endpoint = os.getenv('COSMOSDB_ENDPOINT')
        key = os.getenv('COSMOSDB_KEY')
        database_name = os.getenv('COSMOSDB_DATABASE_NAME', 'ai_brainstorming')
        container_name = os.getenv('COSMOSDB_CONTAINER_NAME', 'chat_sessions')
        
        if not endpoint or not key:
            print("✗ CosmosDB credentials not available")
            return False
        
        # 非同期クライアント作成
        async with AsyncCosmosClient(endpoint, key) as client:
            print("✓ AsyncCosmosClient created successfully")
            
            # データベース接続テスト
            try:
                database = client.get_database_client(database_name)
                db_info = await database.read()
                print(f"✓ Async database '{database_name}' accessible")
            except exceptions.CosmosResourceNotFoundError:
                print(f"✗ Async database '{database_name}' not found")
                return False
            except Exception as e:
                print(f"✗ Async database access failed: {e}")
                return False
            
            # コンテナ接続テスト
            try:
                container = database.get_container_client(container_name)
                container_info = await container.read()
                print(f"✓ Async container '{container_name}' accessible")
            except exceptions.CosmosResourceNotFoundError:
                print(f"✗ Async container '{container_name}' not found")
                return False
            except Exception as e:
                print(f"✗ Async container access failed: {e}")
                return False
            
            # テストドキュメントの作成・読み取り・削除
            try:
                test_doc = {
                    "id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "session_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "type": "connection_test",
                    "message": "This is a connection test document",
                    "timestamp": datetime.now().isoformat(),
                    "ttl": 300  # 5分後に自動削除
                }
                
                # ドキュメント作成
                created_doc = await container.create_item(test_doc)
                print(f"✓ Test document created: {created_doc['id']}")
                
                # ドキュメント読み取り
                read_doc = await container.read_item(
                    item=test_doc['id'],
                    partition_key=test_doc['session_id']
                )
                print(f"✓ Test document read successfully")
                
                # ドキュメント削除
                await container.delete_item(
                    item=test_doc['id'],
                    partition_key=test_doc['session_id']
                )
                print(f"✓ Test document deleted successfully")
                
            except Exception as e:
                print(f"✗ Document operation failed: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Async connection test failed: {e}")
        return False

def test_cosmosdb_manager():
    """CosmosDBManagerクラスのテスト"""
    print("\n=== CosmosDBManager Test ===")
    
    try:
        from src.core.cosmosdb_manager import CosmosDBManager
        
        # テスト設定
        settings = {
            'enabled': os.getenv('COSMOSDB_ENABLED', 'false').lower() == 'true',
            'endpoint': os.getenv('COSMOSDB_ENDPOINT', ''),
            'key': os.getenv('COSMOSDB_KEY', ''),
            'database_name': os.getenv('COSMOSDB_DATABASE_NAME', 'ai_brainstorming'),
            'container_name': os.getenv('COSMOSDB_CONTAINER_NAME', 'chat_sessions')
        }
        
        # CosmosDBManagerインスタンス作成
        manager = CosmosDBManager(settings)
        print("✓ CosmosDBManager created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ CosmosDBManager test failed: {e}")
        return False

async def run_async_tests():
    """非同期テストの実行"""
    return await test_async_connection()

def main():
    """メインテスト実行"""
    print("CosmosDB Connection Test")
    print("=" * 50)
    
    # テスト実行
    tests = [
        ("Import Test", test_import),
        ("Environment Test", test_environment),
        ("Sync Connection Test", test_sync_connection),
        ("CosmosDBManager Test", test_cosmosdb_manager),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # 非同期テスト
    try:
        async_result = asyncio.run(run_async_tests())
        results.append(("Async Connection Test", async_result))
    except Exception as e:
        print(f"✗ Async Connection Test failed with exception: {e}")
        results.append(("Async Connection Test", False))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        icon = "✓" if result else "✗"
        print(f"{icon} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! CosmosDB is ready to use.")
    else:
        print("❌ Some tests failed. Please check the configuration.")
        print("\nTroubleshooting:")
        print("1. Make sure azure-cosmos and aiohttp are installed:")
        print("   pip install azure-cosmos aiohttp")
        print("2. Check your .env file has correct CosmosDB settings")
        print("3. Verify your CosmosDB account, database, and container exist")
        print("4. Run setup script: python scripts/setup_cosmosdb.py")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)