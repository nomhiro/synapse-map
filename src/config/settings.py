"""
Settings - アプリケーション設定管理
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class Settings:
    """アプリケーション設定クラス"""
    
    # Azure OpenAI 設定
    azure_deployment_chat: str
    azure_deployment_reasoning: str
    azure_endpoint: str
    azure_api_key: str
    azure_api_version: str = "2025-04-01-preview"
    
    # モデル設定
    max_tokens_chat: int = 500
    max_tokens_reasoning: int = 2000
    
    # 会話設定
    max_messages: int = 100
    reflection_agent_max_count: int = 3
    allow_repeated_speaker: bool = False
    
    # ログ設定
    log_directory: str = "logs"
    log_level: str = "INFO"
    
    # CosmosDB設定
    cosmosdb_enabled: bool = False
    cosmosdb_endpoint: str = ""
    cosmosdb_key: str = ""
    cosmosdb_database_name: str = "ai_brainstorming"
    cosmosdb_container_name: str = "chat_sessions"
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """環境変数から設定を読み込む"""
        return cls(
            azure_deployment_chat=os.environ["AOAI_DEPLOYMENT_CHAT"],
            azure_deployment_reasoning=os.environ["AOAI_DEPLOYMENT_REASONING"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_api_version=os.environ.get("AZURE_API_VERSION", "2025-04-01-preview"),
            max_tokens_chat=int(os.environ.get("MAX_TOKENS_CHAT", "500")),
            max_tokens_reasoning=int(os.environ.get("MAX_TOKENS_REASONING", "2000")),
            max_messages=int(os.environ.get("MAX_MESSAGES", "100")),
            reflection_agent_max_count=int(os.environ.get("REFLECTION_AGENT_MAX_COUNT", "3")),
            allow_repeated_speaker=os.environ.get("ALLOW_REPEATED_SPEAKER", "false").lower() == "true",
            log_directory=os.environ.get("LOG_DIRECTORY", "logs"),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            cosmosdb_enabled=os.environ.get("COSMOSDB_ENABLED", "false").lower() == "true",
            cosmosdb_endpoint=os.environ.get("COSMOSDB_ENDPOINT", ""),
            cosmosdb_key=os.environ.get("COSMOSDB_KEY", ""),
            cosmosdb_database_name=os.environ.get("COSMOSDB_DATABASE_NAME", "ai_brainstorming"),
            cosmosdb_container_name=os.environ.get("COSMOSDB_CONTAINER_NAME", "chat_sessions")
        )
    
    def validate(self) -> None:
        """設定の妥当性をチェック"""
        required_fields = [
            "azure_deployment_chat",
            "azure_deployment_reasoning", 
            "azure_endpoint",
            "azure_api_key"
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Required setting '{field}' is missing or empty")
        
        if self.max_tokens_chat <= 0:
            raise ValueError("max_tokens_chat must be greater than 0")
        
        if self.max_tokens_reasoning <= 0:
            raise ValueError("max_tokens_reasoning must be greater than 0")
        
        if self.max_messages <= 0:
            raise ValueError("max_messages must be greater than 0")
        
        if self.reflection_agent_max_count <= 0:
            raise ValueError("reflection_agent_max_count must be greater than 0")
        
        # CosmosDB設定の検証
        if self.cosmosdb_enabled:
            if not self.cosmosdb_endpoint:
                raise ValueError("cosmosdb_endpoint is required when CosmosDB is enabled")
            if not self.cosmosdb_key:
                raise ValueError("cosmosdb_key is required when CosmosDB is enabled")
            if not self.cosmosdb_database_name:
                raise ValueError("cosmosdb_database_name is required when CosmosDB is enabled")
            if not self.cosmosdb_container_name:
                raise ValueError("cosmosdb_container_name is required when CosmosDB is enabled")