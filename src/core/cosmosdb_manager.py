"""
CosmosDB Manager - CosmosDBとのリアルタイム連携管理
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from azure.cosmos import CosmosClient, exceptions
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient

from utils.logging import get_logger
from utils.file_utils import format_timestamp


class CosmosDBManager:
    """CosmosDBとのリアルタイム連携を管理するクラス"""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.logger = get_logger(__name__)
        self.client: Optional[AsyncCosmosClient] = None
        self.database = None
        self.container = None
        self.session_id: Optional[str] = None
        self.session_document_id: Optional[str] = None
        
    async def initialize(self) -> bool:
        """CosmosDBクライアントを初期化する"""
        try:
            if not self.settings.get('enabled', False):
                self.logger.info("CosmosDB integration is disabled")
                return False
                
            endpoint = self.settings['endpoint']
            key = self.settings['key']
            database_name = self.settings['database_name']
            container_name = self.settings['container_name']
            
            self.client = AsyncCosmosClient(endpoint, key)
            self.database = self.client.get_database_client(database_name)
            self.container = self.database.get_container_client(container_name)
            
            # セッションIDを生成
            self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self)}"
            
            self.logger.info(f"CosmosDB initialized - Session ID: {self.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CosmosDB: {e}")
            return False
    
    async def create_session_document(self, task: str, team_info: Dict[str, Any]) -> bool:
        """セッション開始時にセッション文書を作成する"""
        try:
            if not self.container:
                return False
                
            now = datetime.now()
            session_doc = {
                "id": self.session_id,
                "session_id": self.session_id,  # パーティションキー
                "type": "session",
                "date": now.strftime("%Y-%m-%d"),  # 日付検索用
                "timestamp": now.timestamp(),      # Unix timestamp検索用
                "task": task,
                "start_time": format_timestamp(),
                "status": "running",
                "team_info": team_info,
                "statistics": {
                    "total_messages": 0,
                    "agent_message_counts": {}
                },
                "created_at": format_timestamp(),
                "updated_at": format_timestamp(),
                "ttl": -1  # Time To Live (無期限)
            }
            
            await self.container.create_item(session_doc)
            self.session_document_id = self.session_id
            
            self.logger.info(f"Session document created: {self.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create session document: {e}")
            return False
    
    async def save_message_realtime(self, message_data: Dict[str, Any]) -> bool:
        """メッセージをリアルタイムでCosmosDBに保存する"""
        try:
            if not self.container or not self.session_document_id:
                return False
            
            # 現在のメッセージ数を取得してシーケンス番号を決定
            current_messages = await self._get_session_messages()
            sequence = len(current_messages) + 1
            
            # メッセージドキュメントを作成
            import time
            unique_id = f"{self.session_id}_msg_{sequence:04d}_{int(time.time() * 1000000)}"
            message_doc = {
                "id": unique_id,
                "session_id": self.session_id,  # パーティションキー
                "type": "message",
                "source": message_data["source"],
                "content": message_data["content"],
                "message_type": message_data["type"],
                "timestamp": message_data["timestamp"],
                "sequence": sequence,  # メッセージ順序
                "created_at": format_timestamp(),
                "ttl": -1
            }
            
            # メッセージドキュメントを作成
            await self.container.create_item(message_doc)
            
            # セッションドキュメントを更新
            await self._update_session_statistics(message_data)
            
            self.logger.debug(f"Message saved to CosmosDB: {message_data['source']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save message to CosmosDB: {e}")
            return False
    
    async def _get_session_messages(self) -> List[Dict[str, Any]]:
        """セッションのメッセージ一覧を取得する"""
        try:
            if not self.container:
                return []
                
            query = f"SELECT * FROM c WHERE c.session_id = '{self.session_id}' AND c.type = 'message' ORDER BY c.sequence"
            items = []
            
            async for item in self.container.query_items(query=query, partition_key=self.session_id):
                items.append(item)
                
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to get session messages: {e}")
            return []
    
    async def _update_session_statistics(self, message_data: Dict[str, Any]) -> bool:
        """セッション統計を更新する"""
        try:
            if not self.container or not self.session_document_id:
                return False
                
            # 現在のセッションドキュメントを取得（パーティションキーはsession_id）
            session_doc = await self.container.read_item(
                item=self.session_document_id,
                partition_key=self.session_id
            )
            
            # 統計を更新
            session_doc["statistics"]["total_messages"] += 1
            
            agent_name = message_data["source"]
            agent_counts = session_doc["statistics"]["agent_message_counts"]
            agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1
            
            session_doc["updated_at"] = format_timestamp()
            
            # ドキュメントを更新
            await self.container.replace_item(
                item=session_doc["id"],
                body=session_doc
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update session statistics: {e}")
            return False
    
    async def complete_session(self, execution_time: float, final_stats: Dict[str, Any]) -> bool:
        """セッション終了時にセッション文書を完了状態に更新する"""
        try:
            if not self.container or not self.session_document_id:
                return False
                
            # セッションドキュメントを取得（パーティションキーはsession_id）
            session_doc = await self.container.read_item(
                item=self.session_document_id,
                partition_key=self.session_id
            )
            
            # 終了情報を更新
            session_doc["status"] = "completed"
            session_doc["end_time"] = format_timestamp()
            session_doc["execution_time"] = execution_time
            session_doc["final_statistics"] = final_stats
            session_doc["updated_at"] = format_timestamp()
            
            # ドキュメントを更新
            await self.container.replace_item(
                item=session_doc["id"],
                body=session_doc
            )
            
            self.logger.info(f"Session completed and saved to CosmosDB: {self.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to complete session in CosmosDB: {e}")
            return False
    
    async def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """過去のセッション履歴を取得する"""
        try:
            if not self.container:
                return []
                
            query = f"SELECT * FROM c WHERE c.type = 'session' ORDER BY c.timestamp DESC OFFSET 0 LIMIT {limit}"
            items = []
            
            async for item in self.container.query_items(query=query, enable_cross_partition_query=True):
                items.append(item)
                
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to get session history: {e}")
            return []
    
    async def health_check(self) -> bool:
        """CosmosDBの接続状態をチェックする"""
        try:
            if not self.container:
                return False
                
            # 簡単なクエリでテスト
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'session'"
            result = []
            async for item in self.container.query_items(query=query, enable_cross_partition_query=True):
                result.append(item)
                
            self.logger.info("CosmosDB health check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"CosmosDB health check failed: {e}")
            return False
    
    async def close(self):
        """CosmosDBクライアントを閉じる"""
        if self.client:
            await self.client.close()
            self.logger.info("CosmosDB client closed")