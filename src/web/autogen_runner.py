"""
AutoGen Runner for Streamlit - StreamlitでAutoGenセッションを実行するためのアダプター
"""

import asyncio
import sys
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import threading
import queue
import time
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# プロジェクトルートをPythonパスに追加
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from core.session_manager import SessionManager
from config.settings import Settings


class StreamlitAutoGenRunner:
    """StreamlitでAutoGenセッションを実行するためのクラス"""
    
    def __init__(self):
        try:
            self.settings = Settings.from_env()
        except (KeyError, ValueError) as e:
            # 環境変数が設定されていない場合はダミー設定
            print(f"Warning: Environment variables not properly set: {e}")
            self.settings = None
        
        self.session_manager = None
        self.current_session_id = None
        self.message_queue = queue.Queue()
        self.is_running = False
        self.session_thread = None
        
    async def initialize(self) -> bool:
        """セッションマネージャーを初期化"""
        try:
            if self.settings is None:
                print("Settings not available - cannot initialize session manager")
                return False
            self.session_manager = SessionManager(self.settings)
            return True
        except Exception as e:
            print(f"Failed to initialize session manager: {e}")
            return False
    
    def start_session_async(self, task: str, callback: Optional[Callable] = None) -> str:
        """非同期でセッションを開始（Streamlitのメインスレッドをブロックしない）"""
        if self.is_running:
            raise RuntimeError("Session is already running")
        
        # セッションIDを生成
        self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.is_running = True
        
        # 別スレッドでセッション実行
        self.session_thread = threading.Thread(
            target=self._run_session_in_thread,
            args=(task, callback),
            daemon=True
        )
        self.session_thread.start()
        
        return self.current_session_id
    
    def _run_session_in_thread(self, task: str, callback: Optional[Callable] = None):
        """別スレッドでセッションを実行"""
        try:
            # 新しいイベントループを作成
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # セッション実行
            loop.run_until_complete(self._run_session_async(task, callback))
            
        except Exception as e:
            self.message_queue.put({
                'type': 'error',
                'content': f'Session execution failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
        finally:
            self.is_running = False
            if callback:
                callback('session_completed')
    
    async def _run_session_async(self, task: str, callback: Optional[Callable] = None):
        """実際のセッション実行"""
        try:
            # セッションマネージャーの初期化
            if not self.session_manager:
                await self.initialize()
            
            # 開始メッセージ
            self.message_queue.put({
                'type': 'system',
                'content': f'Starting AI Brainstorming Session: {task}',
                'timestamp': datetime.now().isoformat()
            })
            
            # セッション実行（メッセージフックを追加）
            await self._run_session_with_message_hook(task)
            
            # 完了メッセージ
            self.message_queue.put({
                'type': 'system',
                'content': 'Session completed successfully!',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.message_queue.put({
                'type': 'error',
                'content': f'Session execution error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
            raise
    
    async def _run_session_with_message_hook(self, task: str):
        """メッセージフック付きでセッションを実行"""
        
        def message_hook(message_data: Dict[str, Any]):
            """メッセージをStreamlitキューに追加するフック"""
            self.message_queue.put({
                'type': 'message',
                'source': message_data.get('source', 'unknown'),
                'content': message_data.get('content', ''),
                'timestamp': message_data.get('timestamp', datetime.now().isoformat())
            })
        
        # メッセージフックを追加
        self.session_manager.add_message_hook(message_hook)
        
        try:
            # セッション実行
            await self.session_manager.run_session(task)
        finally:
            # メッセージフックを削除
            self.session_manager.remove_message_hook(message_hook)
    
    def get_new_messages(self) -> List[Dict[str, Any]]:
        """新しいメッセージを取得"""
        messages = []
        while not self.message_queue.empty():
            try:
                message = self.message_queue.get_nowait()
                messages.append(message)
            except queue.Empty:
                break
        return messages
    
    def is_session_running(self) -> bool:
        """セッションが実行中かどうかを確認"""
        return self.is_running
    
    def get_current_session_id(self) -> Optional[str]:
        """現在のセッションIDを取得"""
        return self.current_session_id
    
    def stop_session(self):
        """セッションを停止"""
        if self.is_running:
            self.is_running = False
            # 注意: この実装では強制停止は困難
            # 実際のAutoGenセッションは自然に終了するまで待つ
    
    async def health_check(self) -> bool:
        """システムの健全性チェック"""
        try:
            if not self.session_manager:
                await self.initialize()
            
            return await self.session_manager.health_check()
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


# Streamlit用のグローバルランナーインスタンス
_runner_instance = None

def get_runner() -> StreamlitAutoGenRunner:
    """グローバルランナーインスタンスを取得"""
    global _runner_instance
    if _runner_instance is None:
        _runner_instance = StreamlitAutoGenRunner()
    return _runner_instance