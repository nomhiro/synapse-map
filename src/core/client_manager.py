"""
Client Manager - AIクライアントの管理
"""

from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from config.settings import Settings
from utils.logging import get_logger
from typing import Optional


class ClientManager:
    """Azure OpenAI クライアントを管理するクラス"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(__name__)
        self._chat_client: Optional[AzureOpenAIChatCompletionClient] = None
        self._reasoning_client: Optional[AzureOpenAIChatCompletionClient] = None
    
    @property
    def chat_client(self) -> AzureOpenAIChatCompletionClient:
        """チャット用クライアントを取得する"""
        if self._chat_client is None:
            self._chat_client = self._create_chat_client()
        return self._chat_client
    
    @property
    def reasoning_client(self) -> AzureOpenAIChatCompletionClient:
        """推論用クライアントを取得する"""
        if self._reasoning_client is None:
            self._reasoning_client = self._create_reasoning_client()
        return self._reasoning_client
    
    def _create_chat_client(self) -> AzureOpenAIChatCompletionClient:
        """チャット用クライアントを作成する"""
        self.logger.info("Creating chat client")
        return AzureOpenAIChatCompletionClient(
            azure_deployment=self.settings.azure_deployment_chat,
            model=self.settings.azure_deployment_chat,
            api_version=self.settings.azure_api_version,
            azure_endpoint=self.settings.azure_endpoint,
            api_key=self.settings.azure_api_key,
            max_tokens=self.settings.max_tokens_chat
        )
    
    def _create_reasoning_client(self) -> AzureOpenAIChatCompletionClient:
        """推論用クライアントを作成する"""
        self.logger.info("Creating reasoning client")
        return AzureOpenAIChatCompletionClient(
            azure_deployment=self.settings.azure_deployment_chat,
            model=self.settings.azure_deployment_reasoning,
            api_version=self.settings.azure_api_version,
            azure_endpoint=self.settings.azure_endpoint,
            api_key=self.settings.azure_api_key,
            max_tokens=self.settings.max_tokens_reasoning
        )
    
    def health_check(self) -> bool:
        """クライアントの健全性をチェックする"""
        try:
            # 簡単なヘルスチェック（実際のAPI呼び出しはしない）
            chat_client = self.chat_client
            reasoning_client = self.reasoning_client
            
            # クライアントが正常に作成されているかチェック
            if chat_client is None or reasoning_client is None:
                return False
            
            self.logger.info("Client health check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Client health check failed: {e}")
            return False
    
    def reset_clients(self) -> None:
        """クライアントをリセットする"""
        self.logger.info("Resetting clients")
        self._chat_client = None
        self._reasoning_client = None