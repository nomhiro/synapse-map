"""
Team Manager - チーム管理とエージェント統合
"""

from typing import List, Dict, Any
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination

from agents import (
        CreativePlannerAgent, MarketAnalystAgent, TechnicalValidatorAgent,
        BusinessEvaluatorAgent, UserAdvocateAgent, ReflectionAgent
    )
from config.settings import Settings
from config.prompts import Prompts
from core.client_manager import ClientManager
from utils.logging import get_logger
from utils.agent_count_termination import AgentCountTermination


class TeamManager:
    """エージェントチームの管理を行うクラス"""
    
    def __init__(self, settings: Settings, client_manager: ClientManager):
        self.settings = settings
        self.client_manager = client_manager
        self.logger = get_logger(__name__)
        self.agents = {}
        self.team = None
        
        self._initialize_agents()
        self._initialize_team()
    
    def _initialize_agents(self) -> None:
        """エージェントを初期化する"""
        self.logger.info("Initializing agents")
        
        chat_client = self.client_manager.chat_client
        
        # 各エージェントのインスタンスを作成
        self.agents = {
            'creative_planner': CreativePlannerAgent(chat_client),
            'market_analyst': MarketAnalystAgent(chat_client),
            'technical_validator': TechnicalValidatorAgent(chat_client),
            'business_evaluator': BusinessEvaluatorAgent(chat_client),
            'user_advocate': UserAdvocateAgent(chat_client),
            'reflection_agent': ReflectionAgent(chat_client)
        }
        
        self.logger.info(f"Initialized {len(self.agents)} agents")
    
    def _initialize_team(self) -> None:
        """チームを初期化する"""
        self.logger.info("Initializing team")
        
        # エージェントリストを作成
        agent_list = [agent.create_agent() for agent in self.agents.values()]
        
        # 終了条件を設定
        max_messages_termination = MaxMessageTermination(
            max_messages=self.settings.max_messages
        )
        reflection_termination = AgentCountTermination(
            agent_name="reflection_agent",
            max_count=self.settings.reflection_agent_max_count
        )
        termination = reflection_termination | max_messages_termination
        
        # セレクタープロンプトを取得
        selector_prompt = Prompts.get_selector_prompt()
        
        # チームを作成
        self.team = SelectorGroupChat(
            agent_list,
            model_client=self.client_manager.reasoning_client,
            termination_condition=termination,
            selector_prompt=selector_prompt,
            allow_repeated_speaker=self.settings.allow_repeated_speaker
        )
        
        self.logger.info("Team initialized successfully")
    
    def get_team(self) -> SelectorGroupChat:
        """チームインスタンスを取得する"""
        if self.team is None:
            self._initialize_team()
        return self.team
    
    def get_agent(self, agent_name: str):
        """指定されたエージェントを取得する"""
        return self.agents.get(agent_name)
    
    def get_agent_list(self) -> List[str]:
        """エージェント名のリストを取得する"""
        return list(self.agents.keys())
    
    def reset_team(self) -> None:
        """チームをリセットする"""
        self.logger.info("Resetting team")
        self.team = None
        self._initialize_team()
    
    def get_team_info(self) -> Dict[str, Any]:
        """チーム情報を取得する"""
        return {
            'agent_count': len(self.agents),
            'agent_names': list(self.agents.keys()),
            'max_messages': self.settings.max_messages,
            'reflection_agent_max_count': self.settings.reflection_agent_max_count,
            'allow_repeated_speaker': self.settings.allow_repeated_speaker
        }