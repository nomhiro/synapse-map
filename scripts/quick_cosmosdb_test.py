"""
Quick CosmosDB Test - 簡単なCosmosDB接続確認
"""

import os
import sys
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def quick_test():
    """クイック接続テスト"""
    print("Quick CosmosDB Connection Test")
    print("-" * 30)
    
    # 1. 依存関係チェック
    print("1. Checking dependencies...")
    try:
        from azure.cosmos import CosmosClient
        print("   ✓ azure-cosmos available")
    except ImportError:
        print("   ✗ azure-cosmos not installed")
        print("   Solution: pip install azure-cosmos")
        return False
    
    try:
        import aiohttp
        print("   ✓ aiohttp available")
    except ImportError:
        print("   ✗ aiohttp not installed")
        print("   Solution: pip install aiohttp")
        return False
    
    # 2. 環境変数チェック
    print("\n2. Checking environment variables...")
    endpoint = os.getenv('COSMOSDB_ENDPOINT')
    key = os.getenv('COSMOSDB_KEY')
    
    if not endpoint:
        print("   ✗ COSMOSDB_ENDPOINT not set")
        return False
    else:
        print(f"   ✓ COSMOSDB_ENDPOINT: {endpoint[:30]}...")
    
    if not key:
        print("   ✗ COSMOSDB_KEY not set")
        return False
    else:
        print(f"   ✓ COSMOSDB_KEY: {key[:8]}...{key[-4:]}")
    
    # 3. 接続テスト
    print("\n3. Testing connection...")
    try:
        client = CosmosClient(endpoint, key)
        
        # データベース一覧取得でテスト
        databases = list(client.list_databases())
        print(f"   ✓ Connected successfully - Found {len(databases)} databases")
        
        # 対象データベースの確認
        database_name = os.getenv('COSMOSDB_DATABASE_NAME', 'ai_brainstorming')
        try:
            database = client.get_database_client(database_name)
            db_info = database.read()
            print(f"   ✓ Database '{database_name}' found")
            
            # コンテナの確認
            container_name = os.getenv('COSMOSDB_CONTAINER_NAME', 'chat_sessions')
            try:
                container = database.get_container_client(container_name)
                container_info = container.read()
                print(f"   ✓ Container '{container_name}' found")
                print(f"   ✓ Partition key: {container_info.get('partitionKey', {}).get('paths', [])}")
                
                return True
                
            except Exception as e:
                print(f"   ✗ Container '{container_name}' not found: {e}")
                print(f"   Solution: Run 'python scripts/setup_cosmosdb.py'")
                return False
                
        except Exception as e:
            print(f"   ✗ Database '{database_name}' not found: {e}")
            print(f"   Solution: Run 'python scripts/setup_cosmosdb.py'")
            return False
            
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("   Check your endpoint and key in .env file")
        return False

def main():
    """メイン実行"""
    success = quick_test()
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 CosmosDB connection successful!")
        print("You can now set COSMOSDB_ENABLED=true")
    else:
        print("❌ CosmosDB connection failed")
        print("Please fix the issues above and try again")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)