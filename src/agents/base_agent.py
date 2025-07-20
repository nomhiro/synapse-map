"""
Base Agent - 全エージェントの基底クラス
"""

from abc import ABC, abstractmethod
from autogen_agentchat.agents import AssistantAgent
from typing import Dict, Any


class BaseAgent(ABC):
    """エージェントの基底クラス"""
    
    def __init__(self, model_client):
        self.model_client = model_client
        self._agent = None
    
    @property
    @abstractmethod
    def agent_name(self) -> str:
        """エージェント名を返す"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """エージェントの説明を返す"""
        pass
    
    @property
    @abstractmethod
    def system_message(self) -> str:
        """システムメッセージを返す"""
        pass
    
    def create_agent(self) -> AssistantAgent:
        """AutoGenのAssistantAgentを作成する"""
        if self._agent is None:
            self._agent = AssistantAgent(
                self.agent_name,
                description=self.description,
                model_client=self.model_client,
                system_message=self.system_message
            )
        return self._agent
    
    def get_common_guidelines(self) -> str:
        """共通の回答方針を返す"""
        return """
        ## 共通回答方針
        - 会話履歴を注意深く確認します
        - 過去に出た意見や提案に重複しないように、新しい視点で意見してください
        - 問い合わせ内容が複数ある場合は、それぞれについて詳細に検討してください
        - 意見は300文字以内で日本語で簡潔に行いましょう
        """