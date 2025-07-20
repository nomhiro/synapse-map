"""
Agent Configs - エージェント設定
"""

from typing import Dict, Any


class AgentConfigs:
    """エージェント設定を管理するクラス"""
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """デフォルトのエージェント設定を取得"""
        return {
            "response_max_length": 300,
            "language": "ja",
            "enable_history_check": True,
            "avoid_repetition": True
        }
    
    @staticmethod
    def get_agent_specific_config(agent_name: str) -> Dict[str, Any]:
        """エージェント固有の設定を取得"""
        configs = {
            "creative_planner": {
                "creativity_level": "high",
                "innovation_focus": True,
                "trend_awareness": True
            },
            "market_analyst": {
                "data_driven": True,
                "competitive_analysis": True,
                "trend_tracking": True
            },
            "technical_validator": {
                "risk_assessment": True,
                "feasibility_focus": True,
                "cost_estimation": True
            },
            "business_evaluator": {
                "roi_focus": True,
                "revenue_analysis": True,
                "risk_evaluation": True
            },
            "user_advocate": {
                "user_centric": True,
                "accessibility_focus": True,
                "satisfaction_priority": True
            },
            "reflection_agent": {
                "topic_generation": True,
                "conversation_analysis": True,
                "discussion_facilitation": True
            }
        }
        
        return configs.get(agent_name, {})