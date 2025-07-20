"""
Session Manager - セッション管理とメイン実行ロジック
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
from autogen_agentchat.base import TaskResult

from config.settings import Settings
from config.prompts import Prompts
from core.client_manager import ClientManager
from core.team_manager import TeamManager
from core.cosmosdb_manager import CosmosDBManager
from utils.logging import get_logger
from utils.file_utils import save_context, format_timestamp
from utils.unicode_utils import safe_print, safe_format_output


class SessionManager:
    """セッション管理とメイン実行ロジックを担当するクラス"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(__name__)
        self.client_manager = ClientManager(settings)
        self.team_manager = TeamManager(settings, self.client_manager)
        
        # CosmosDB設定
        cosmosdb_settings = {
            'enabled': settings.cosmosdb_enabled,
            'endpoint': settings.cosmosdb_endpoint,
            'key': settings.cosmosdb_key,
            'database_name': settings.cosmosdb_database_name,
            'container_name': settings.cosmosdb_container_name
        }
        self.cosmosdb_manager = CosmosDBManager(cosmosdb_settings)
        
        self.chat_contexts: List[Dict[str, Any]] = []
        self.session_start_time: Optional[float] = None
    
    async def run_session(self, task: Optional[str] = None) -> str:
        """セッションを実行する"""
        self.logger.info("Starting new session")
        self.session_start_time = time.time()
        
        if task is None:
            task = Prompts.get_default_task()
        
        self.logger.info(f"Task: {task}")
        
        try:
            # CosmosDBを初期化
            await self.cosmosdb_manager.initialize()
            
            # チームを取得
            team = self.team_manager.get_team()
            
            # CosmosDBにセッション文書を作成
            if self.cosmosdb_manager.container:
                await self.cosmosdb_manager.create_session_document(
                    task, 
                    self.team_manager.get_team_info()
                )
            
            # セッション実行
            await self._execute_session(team, task)
            
            # 結果を保存
            filename = save_context(self.chat_contexts, self.settings.log_directory)
            
            execution_time = time.time() - self.session_start_time
            
            # CosmosDBでセッション完了
            if self.cosmosdb_manager.container:
                final_stats = self.get_session_stats()
                await self.cosmosdb_manager.complete_session(execution_time, final_stats)
            
            self.logger.info(f"Session completed in {execution_time:.2f} seconds")
            safe_print(f"Context saved to {filename}")
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Session failed: {e}")
            raise
        finally:
            # CosmosDBクライアントを閉じる
            await self.cosmosdb_manager.close()
    
    async def _execute_session(self, team, task: str) -> None:
        """セッションを実行する内部メソッド"""
        self.chat_contexts.clear()
        
        async for chunk in team.run_stream(task=task):
            if isinstance(chunk, TaskResult):
                safe_print(f"Stop reason: {chunk.stop_reason}")
                self.logger.info(f"Session ended with reason: {chunk.stop_reason}")
            else:
                # 出力を安全に表示（詳細ログを抑制してユーザーメッセージのみ）
                if chunk.type == "TextMessage":
                    formatted_output = safe_format_output(chunk.source, chunk.type, chunk.content)
                    safe_print(formatted_output)
                
                # テキストメッセージの場合はコンテキストに保存
                if chunk.type == "TextMessage":
                    chat_context = {
                        "source": chunk.source,
                        "content": chunk.content,
                        "type": chunk.type,
                        "timestamp": format_timestamp()
                    }
                    self.chat_contexts.append(chat_context)
                    
                    # CosmosDBにリアルタイム保存
                    if self.cosmosdb_manager.container:
                        try:
                            await self.cosmosdb_manager.save_message_realtime(chat_context)
                        except Exception as db_error:
                            self.logger.warning(f"Failed to save message to CosmosDB: {db_error}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """セッション統計を取得する"""
        if self.session_start_time is None:
            return {"status": "not_started"}
        
        execution_time = time.time() - self.session_start_time
        
        # エージェント別メッセージ数を集計
        agent_message_counts = {}
        for context in self.chat_contexts:
            source = context.get("source", "unknown")
            agent_message_counts[source] = agent_message_counts.get(source, 0) + 1
        
        return {
            "status": "completed",
            "execution_time": execution_time,
            "execution_time_formatted": f"{execution_time:.2f}s",
            "session_start": format_timestamp(datetime.fromtimestamp(self.session_start_time)),
            "session_end": format_timestamp(),
            "total_messages": len(self.chat_contexts),
            "agent_message_counts": agent_message_counts,
            "team_info": self.team_manager.get_team_info()
        }
    
    def get_chat_contexts(self) -> List[Dict[str, Any]]:
        """チャットコンテキストを取得する"""
        return self.chat_contexts.copy()
    
    def reset_session(self) -> None:
        """セッションをリセットする"""
        self.logger.info("Resetting session")
        self.chat_contexts.clear()
        self.session_start_time = None
        self.team_manager.reset_team()
    
    async def health_check(self) -> bool:
        """システムの健全性をチェックする"""
        try:
            # クライアントの健全性チェック
            if not self.client_manager.health_check():
                return False
            
            # チームの健全性チェック
            team = self.team_manager.get_team()
            if team is None:
                return False
            
            # CosmosDBの健全性チェック（有効な場合のみ）
            if self.settings.cosmosdb_enabled:
                await self.cosmosdb_manager.initialize()
                if not await self.cosmosdb_manager.health_check():
                    self.logger.warning("CosmosDB health check failed, but system will continue")
                await self.cosmosdb_manager.close()
            
            self.logger.info("System health check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"System health check failed: {e}")
            return False