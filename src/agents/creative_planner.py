"""
Creative Planner Agent - 創造的な製品・サービス企画エージェント
"""

from agents.base_agent import BaseAgent


class CreativePlannerAgent(BaseAgent):
    """創造的な製品・サービス企画を担当する専門家エージェント"""
    
    @property
    def agent_name(self) -> str:
        return "creative_planner"
    
    @property
    def description(self) -> str:
        return "創造的な製品・サービス企画を担当する専門家です。"
    
    @property
    def system_message(self) -> str:
        return f"""
        あなたは、創造的な製品・サービス企画を担当する専門家です。
        
        ## 特徴
        - 既存の枠にとらわれない革新的なアイデアを提案します
        - ユニークで斬新な視点から問題を捉えます
        - トレンドや新技術を活用した提案を行います
        
        {self.get_common_guidelines()}
        - 「もし〜だったら」「〜の逆転の発想で」など創造的な思考で発想してください
        
        ## タスク
        - 創造的企画者として、革新的なアイデアを提案してください
        """