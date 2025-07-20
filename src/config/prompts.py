"""
Prompts - プロンプトテンプレート管理
"""

from typing import Dict, List


class Prompts:
    """プロンプトテンプレートを管理するクラス"""
    
    @staticmethod
    def get_selector_prompt() -> str:
        """エージェント選択のプロンプトを取得"""
        return """次のタスクを実行するエージェントを選択してください。
    {roles}
    会話履歴:
    {history}
    
    ## タスク
    - 上記の会話履歴を確認します。
    - 3回続けて賛成意見が出た場合、reflection_agentを選択して、新たなトピックでディスカッションを始めてください。それ以外の場合にはreflection_agentを選択しないでください。
    - 会話履歴を読んだ上で、 [creative_planner, market_analyst, technical_validator, business_evaluator, user_advocate]の中から次のタスクを実行するエージェントを1人選んでください。
    - エージェントを選ぶ際は、今の会話に対して新しいアイデアを提供できるエージェントを選んでください。
    - 必ず1人だけ選択してください。
    """
    
    @staticmethod
    def get_default_task() -> str:
        """デフォルトのタスクを取得"""
        return """新しいモバイルアプリサービスの企画を検討します。リモートワーク時代に対応した、チームコミュニケーションを大幅に改善する革新的なサービスを開発したいと考えています。各専門家の立場からディスカッションを行い、新しいアイデアを生み出してください。"""
    
    @staticmethod
    def get_agent_list() -> List[str]:
        """エージェントのリストを取得"""
        return [
            "creative_planner",
            "market_analyst", 
            "technical_validator",
            "business_evaluator",
            "user_advocate"
        ]