# 実装時の工夫とハマりポイント

開発過程で遭遇した技術的課題とその解決方法を、実際のコード例とともに詳しく解説します。これらの経験が同様のシステムを開発する方の参考になれば幸いです。

## Unicode文字エンコーディング問題

### 問題の発生

AutoGenを日本語環境で使用すると、コンソール出力で文字化けが発生しました：

```
# 文字化けの例
[2024-01-20 14:30:22] creative_planner: ????????????????????????????
[2024-01-20 14:30:23] market_analyst: ??????????????????
```

### 原因分析

AutoGenの内部ログ出力が、Windowsのコンソールエンコーディング（CP932）と不整合を起こしていました。特に以下の場面で問題が発生：

1. エージェント名に日本語を含む場合
2. システムメッセージに日本語を含む場合  
3. AutoGenの詳細ログ出力時

### 解決策1: 安全な出力関数の実装

```python
import sys
import unicodedata

def safe_print(message: str, end: str = "\n", file=None):
    """エンコーディングエラーを回避する安全な出力関数"""
    if file is None:
        file = sys.stdout
    
    try:
        # 通常の出力を試行
        print(message, end=end, file=file)
        
    except UnicodeEncodeError:
        try:
            # エンコーディング安全な形式に変換
            safe_message = message.encode('ascii', errors='replace').decode('ascii')
            print(f"[エンコーディング調整] {safe_message}", end=end, file=file)
            
        except Exception:
            # 最終フォールバック
            simplified = unicodedata.normalize('NFKC', message)
            ascii_only = ''.join(c if ord(c) < 128 else '?' for c in simplified)
            print(f"[ASCII変換] {ascii_only}", end=end, file=file)

def safe_format_message(source: str, content: str, timestamp: str = None) -> str:
    """安全なメッセージフォーマット"""
    try:
        if timestamp:
            return f"[{timestamp}] {source}: {content}"
        else:
            return f"{source}: {content}"
    except UnicodeEncodeError:
        # 安全な文字のみ使用
        safe_source = source.encode('ascii', errors='replace').decode('ascii')
        safe_content = content.encode('ascii', errors='replace').decode('ascii')
        return f"{safe_source}: {safe_content}"
```

### 解決策2: AutoGenログの制御

```python
import logging

def configure_autogen_logging():
    """AutoGenのログ設定を最適化"""
    
    # AutoGenの詳細ログを抑制
    logging.getLogger("autogen").setLevel(logging.WARNING)
    logging.getLogger("autogen_agentchat").setLevel(logging.WARNING)
    
    # カスタムフォーマッターを設定
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コンソールハンドラーを設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # ルートロガーに追加
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)
```

## インポートパス管理の課題

### 問題の発生

Streamlitアプリケーション実行時に、相対インポートエラーが頻発しました：

```python
# エラーの例
ModuleNotFoundError: No module named 'src.core.session_manager'
ImportError: attempted relative import with no known parent package
```

### 原因分析

Streamlitの実行環境では、Pythonの実行コンテキストが通常とは異なるため、以下の問題が発生：

1. `streamlit run`での実行時、スクリプトが直接実行される
2. 相対インポートの基準パスが不明確
3. `sys.path`にプロジェクトルートが含まれない

### 解決策: 動的パス解決システム

```python
# src/web/streamlit_app.py の冒頭
import sys
import os
from pathlib import Path

def setup_import_paths():
    """インポートパスを動的に設定"""
    
    # 現在のファイルから相対的にプロジェクトルートを特定
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # 3階層上がプロジェクトルート
    
    # プロジェクトルートを sys.path に追加
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 確認用出力
    print(f"プロジェクトルート: {project_root}")
    print(f"現在のsys.path: {sys.path[:3]}...")  # 最初の3つだけ表示

# 最初に実行
setup_import_paths()

# これで絶対インポートが可能になる
try:
    from src.core.session_manager import SessionManager
    from src.core.settings import Settings
    from src.web.autogen_runner import StreamlitAutoGenRunner
except ImportError as e:
    print(f"インポートエラー: {e}")
    
    # フォールバック: 相対インポート
    try:
        from ..core.session_manager import SessionManager
        from ..core.settings import Settings
        from .autogen_runner import StreamlitAutoGenRunner
    except ImportError as e2:
        print(f"相対インポートも失敗: {e2}")
        sys.exit(1)
```

### __init__.py ファイルの適切な設定

```python
# src/__init__.py
"""AIブレインストーミングシステム"""

# src/core/__init__.py
"""コアモジュール"""
from .session_manager import SessionManager
from .settings import Settings
from .cosmosdb_manager import CosmosDBManager

__all__ = ['SessionManager', 'Settings', 'CosmosDBManager']

# src/web/__init__.py  
"""Webアプリケーションモジュール"""
from .streamlit_app import main
from .autogen_runner import StreamlitAutoGenRunner

__all__ = ['main', 'StreamlitAutoGenRunner']
```

## 環境変数管理の改善

### 問題の発生

開発環境と本番環境での設定管理が煩雑で、以下の問題が発生：

1. 環境変数の読み込み失敗
2. デフォルト値の不整合
3. 機密情報の誤ったハードコーディング

### 解決策: 堅牢な設定管理システム

```python
import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Settings:
    """アプリケーション設定"""
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_model: str
    azure_openai_api_version: str
    cosmosdb_endpoint: str
    cosmosdb_key: str
    cosmosdb_database_name: str
    cosmosdb_container_name: str
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'Settings':
        """環境変数から設定を読み込み（.envファイル対応）"""
        
        # .envファイルを読み込み
        if env_file:
            load_env_file(env_file)
        else:
            # デフォルトの.envファイルを探索
            possible_env_files = [
                Path.cwd() / ".env",
                Path.cwd() / "config" / ".env",
                Path(__file__).parent.parent.parent / ".env"
            ]
            
            for env_path in possible_env_files:
                if env_path.exists():
                    load_env_file(str(env_path))
                    break
        
        # 必須環境変数のチェック
        required_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY", 
            "COSMOSDB_ENDPOINT",
            "COSMOSDB_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise EnvironmentError(
                f"必須環境変数が設定されていません: {', '.join(missing_vars)}\n"
                f"設定例:\n"
                f"AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/\n"
                f"AZURE_OPENAI_API_KEY=your-api-key"
            )
        
        # 設定オブジェクトを作成
        return cls(
            azure_openai_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_openai_model=os.environ.get("AZURE_OPENAI_MODEL", "gpt-4"),
            azure_openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            cosmosdb_endpoint=os.environ["COSMOSDB_ENDPOINT"],
            cosmosdb_key=os.environ["COSMOSDB_KEY"],
            cosmosdb_database_name=os.environ.get("COSMOSDB_DATABASE_NAME", "brainstorming_db"),
            cosmosdb_container_name=os.environ.get("COSMOSDB_CONTAINER_NAME", "sessions")
        )
    
    def validate(self) -> bool:
        """設定値の妥当性をチェック"""
        try:
            # URLの形式チェック
            if not self.azure_openai_endpoint.startswith("https://"):
                raise ValueError("Azure OpenAI エンドポイントはHTTPSで始まる必要があります")
            
            if not self.cosmosdb_endpoint.startswith("https://"):
                raise ValueError("CosmosDB エンドポイントはHTTPSで始まる必要があります")
            
            # API キーの最小長チェック
            if len(self.azure_openai_api_key) < 10:
                raise ValueError("Azure OpenAI API キーが短すぎます")
            
            if len(self.cosmosdb_key) < 10:
                raise ValueError("CosmosDB キーが短すぎます")
            
            return True
            
        except ValueError as e:
            print(f"設定値エラー: {e}")
            return False

def load_env_file(file_path: str):
    """手動で.envファイルを読み込み（python-dotenvの代替）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # コメント行と空行をスキップ
                if not line or line.startswith('#'):
                    continue
                
                # KEY=VALUE形式のパース
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")  # クォートを除去
                    
                    # 環境変数として設定
                    os.environ[key] = value
                else:
                    print(f"警告: {file_path}:{line_num} - 無効な形式: {line}")
                    
    except FileNotFoundError:
        print(f"環境ファイルが見つかりません: {file_path}")
    except Exception as e:
        print(f"環境ファイル読み込みエラー: {e}")
```

## CosmosDB接続の安定化

### 問題の発生

CosmosDBへの接続で以下のエラーが断続的に発生：

```python
# よくあるエラー
azure.cosmos.exceptions.CosmosHttpResponseError: (429) Request rate is large
azure.cosmos.exceptions.CosmosResourceNotFoundError: Entity with the specified id does not exist
azure.cosmos.exceptions.CosmosResourceExistsError: Entity with the specified id already exists
```

### 解決策: 包括的エラーハンドリング

```python
import asyncio
import random
from azure.cosmos import exceptions as cosmos_exceptions

class RobustCosmosDBManager:
    """堅牢なCosmosDB接続管理"""
    
    async def save_with_retry(self, document: dict, max_retries: int = 5):
        """リトライ機能付きドキュメント保存"""
        
        for attempt in range(max_retries):
            try:
                return await self.container.create_item(document)
                
            except cosmos_exceptions.CosmosResourceExistsError:
                # ID重複の場合、新しいIDを生成
                document["id"] = self._generate_unique_id(document)
                continue
                
            except cosmos_exceptions.CosmosHttpResponseError as e:
                if e.status_code == 429:  # Rate limit
                    # 指数バックオフ + ジッター
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    safe_print(f"レート制限エラー、{wait_time:.1f}秒待機中...")
                    await asyncio.sleep(wait_time)
                    continue
                    
                elif e.status_code == 503:  # Service unavailable
                    wait_time = min(2 ** attempt, 30)  # 最大30秒
                    safe_print(f"サービス利用不可、{wait_time}秒待機中...")
                    await asyncio.sleep(wait_time)
                    continue
                    
                else:
                    safe_print(f"CosmosDBエラー ({e.status_code}): {e.message}")
                    raise
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    safe_print(f"保存失敗（最終試行）: {e}")
                    raise
                else:
                    safe_print(f"保存エラー（試行{attempt + 1}）: {e}")
                    await asyncio.sleep(1)
        
        raise Exception(f"最大リトライ回数（{max_retries}）に達しました")
    
    def _generate_unique_id(self, document: dict) -> str:
        """重複を避けるユニークID生成"""
        base_id = document.get("id", "unknown")
        timestamp = int(time.time() * 1000000)  # マイクロ秒
        random_suffix = random.randint(1000, 9999)
        
        return f"{base_id}_{timestamp}_{random_suffix}"
    
    async def query_with_fallback(self, query: str, parameters: list = None):
        """フォールバック機能付きクエリ実行"""
        try:
            # 通常のクエリ実行
            items = []
            async for item in self.container.query_items(
                query=query,
                parameters=parameters or [],
                enable_cross_partition_query=True
            ):
                items.append(item)
            return items
            
        except cosmos_exceptions.CosmosHttpResponseError as e:
            if e.status_code == 429:
                safe_print("クエリレート制限、簡略化クエリで再試行...")
                # より簡単なクエリにフォールバック
                fallback_query = "SELECT * FROM c WHERE c.type = 'session_info'"
                return await self._execute_simple_query(fallback_query)
            else:
                raise
                
        except Exception as e:
            safe_print(f"クエリエラー: {e}")
            return []
    
    async def health_check(self) -> bool:
        """接続健全性チェック"""
        try:
            # 軽量なクエリで接続テスト
            test_query = "SELECT TOP 1 c.id FROM c"
            await self.container.query_items(
                query=test_query,
                enable_cross_partition_query=True
            ).__anext__()
            return True
            
        except Exception as e:
            safe_print(f"ヘルスチェック失敗: {e}")
            return False
```

## Streamlit特有の制約への対処

### 問題: セッション状態の複雑性

Streamlitの`session_state`管理で以下の問題が発生：

1. ページ間での状態の不整合
2. 非同期処理との組み合わせでの競合状態
3. メモリリークの懸念

### 解決策: 状態管理の標準化

```python
class StreamlitStateManager:
    """Streamlit状態管理の標準化"""
    
    @staticmethod
    def initialize_session_state():
        """セッション状態の初期化"""
        default_state = {
            'runner': None,
            'live_messages': [],
            'session_running': False,
            'current_session_id': None,
            'session_history': [],
            'selected_session_id': None,
            'error_count': 0,
            'last_update': None
        }
        
        for key, default_value in default_state.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def reset_session_state(preserve_keys: list = None):
        """セッション状態のリセット（指定キーは保持）"""
        preserve_keys = preserve_keys or ['session_history']
        preserved_values = {}
        
        # 保持する値を退避
        for key in preserve_keys:
            if key in st.session_state:
                preserved_values[key] = st.session_state[key]
        
        # 全状態をクリア
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # 初期化後、保持する値を復元
        StreamlitStateManager.initialize_session_state()
        for key, value in preserved_values.items():
            st.session_state[key] = value
    
    @staticmethod
    def safe_update_state(key: str, value, callback=None):
        """安全な状態更新"""
        try:
            old_value = st.session_state.get(key)
            st.session_state[key] = value
            
            if callback:
                callback(old_value, value)
                
        except Exception as e:
            safe_print(f"状態更新エラー ({key}): {e}")
            # ロールバック
            if old_value is not None:
                st.session_state[key] = old_value
```

これらの経験と解決策により、安定性と保守性の高いシステムを構築できました。次のセクションでは、パフォーマンス最適化について詳しく解説します。