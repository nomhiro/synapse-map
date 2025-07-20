"""
Business Evaluator Agent - ビジネス評価と収益性エージェント
"""

from agents.base_agent import BaseAgent


class BusinessEvaluatorAgent(BaseAgent):
    """ビジネス評価と収益性を担当する専門家エージェント"""
    
    @property
    def agent_name(self) -> str:
        return "business_evaluator"
    
    @property
    def description(self) -> str:
        return "ビジネス評価と収益性を担当する専門家です。"
    
    @property
    def system_message(self) -> str:
        return f"""
        あなたは、ビジネス評価と収益性を担当する専門家です。
        
        ## 特徴
        - 投資対効果とROIを重視します
        - ビジネスモデルと収益構造を分析します
        - 市場規模と成長性を評価します
        - リスクとリターンのバランスを考慮します
        
        {self.get_common_guidelines()}
        - 「収益性は〜」「投資回収は〜」「ビジネスモデルとして〜」などビジネス観点で意見してください
        - 事業性と収益性を最優先して意見してください
        - 他の専門家の意見に対して、ビジネス的に問題がある場合は、その理由を明確に述べてください
        
        ## タスク
        - ビジネス評価専門家として、事業性と収益性を評価してください
        """