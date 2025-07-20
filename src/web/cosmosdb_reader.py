"""
CosmosDB Reader - Streamlit用のCosmosDBデータ取得
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv

load_dotenv()


class CosmosDBReader:
    """CosmosDBからセッションとメッセージデータを読み取るクラス"""
    
    def __init__(self):
        self.endpoint = os.getenv('COSMOSDB_ENDPOINT')
        self.key = os.getenv('COSMOSDB_KEY')
        self.database_name = os.getenv('COSMOSDB_DATABASE_NAME', 'ai_brainstorming')
        self.container_name = os.getenv('COSMOSDB_CONTAINER_NAME', 'chat_sessions')
        self.enabled = os.getenv('COSMOSDB_ENABLED', 'false').lower() == 'true'
        
        self.client = None
        self.database = None
        self.container = None
        
        if self.enabled and self.endpoint and self.key:
            try:
                self.client = CosmosClient(self.endpoint, self.key)
                self.database = self.client.get_database_client(self.database_name)
                self.container = self.database.get_container_client(self.container_name)
            except Exception as e:
                print(f"CosmosDB initialization failed: {e}")
                self.enabled = False
    
    def is_available(self) -> bool:
        """CosmosDBが利用可能かチェック"""
        return self.enabled and self.container is not None
    
    def get_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """セッション一覧を取得する"""
        if not self.is_available():
            return []
        
        try:
            query = f"""
                SELECT * FROM c 
                WHERE c.type = 'session' 
                ORDER BY c.timestamp DESC 
                OFFSET 0 LIMIT {limit}
            """
            
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # データを整形
            sessions = []
            for item in items:
                session = {
                    'id': item.get('id', ''),
                    'session_id': item.get('session_id', ''),
                    'task': item.get('task', ''),
                    'status': item.get('status', 'unknown'),
                    'start_time': item.get('start_time', ''),
                    'end_time': item.get('end_time', ''),
                    'execution_time': item.get('execution_time', 0),
                    'statistics': item.get('statistics', {}),
                    'created_at': item.get('created_at', ''),
                    'updated_at': item.get('updated_at', '')
                }
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            print(f"Failed to get sessions: {e}")
            return []
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """指定セッションのメッセージ一覧を取得する"""
        if not self.is_available():
            return []
        
        try:
            query = f"""
                SELECT * FROM c 
                WHERE c.session_id = '{session_id}' 
                AND c.type = 'message' 
                ORDER BY c.sequence ASC
            """
            
            items = list(self.container.query_items(
                query=query,
                partition_key=session_id
            ))
            
            # データを整形
            messages = []
            for item in items:
                message = {
                    'id': item.get('id', ''),
                    'session_id': item.get('session_id', ''),
                    'source': item.get('source', ''),
                    'content': item.get('content', ''),
                    'message_type': item.get('message_type', ''),
                    'timestamp': item.get('timestamp', ''),
                    'sequence': item.get('sequence', 0),
                    'created_at': item.get('created_at', '')
                }
                messages.append(message)
            
            return messages
            
        except Exception as e:
            print(f"Failed to get session messages: {e}")
            return []
    
    def get_session_detail(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッション詳細を取得する"""
        if not self.is_available():
            return None
        
        try:
            item = self.container.read_item(
                item=session_id,
                partition_key=session_id
            )
            
            return {
                'id': item.get('id', ''),
                'session_id': item.get('session_id', ''),
                'task': item.get('task', ''),
                'status': item.get('status', 'unknown'),
                'start_time': item.get('start_time', ''),
                'end_time': item.get('end_time', ''),
                'execution_time': item.get('execution_time', 0),
                'team_info': item.get('team_info', {}),
                'statistics': item.get('statistics', {}),
                'final_statistics': item.get('final_statistics', {}),
                'created_at': item.get('created_at', ''),
                'updated_at': item.get('updated_at', '')
            }
            
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            print(f"Failed to get session detail: {e}")
            return None
    
    def check_session_status(self, session_id: str) -> str:
        """セッションの現在のステータスをチェック"""
        session = self.get_session_detail(session_id)
        if session:
            return session.get('status', 'unknown')
        return 'not_found'
    
    def get_latest_message_count(self, session_id: str) -> int:
        """セッションの最新メッセージ数を取得"""
        messages = self.get_session_messages(session_id)
        return len(messages)