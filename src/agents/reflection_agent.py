"""
Reflection Agent - 会話内容を振り返り新しいトピックを提案するエージェント
"""

from agents.base_agent import BaseAgent


class ReflectionAgent(BaseAgent):
    """会話内容から新しいトピックを提案する専門家エージェント"""
    
    @property
    def agent_name(self) -> str:
        return "reflection_agent"
    
    @property
    def description(self) -> str:
        return "他のエージェントから3回続けて賛成意見が出た場合にのみ選択可能です。これまでの会話内容から新しいトピックを提案します。"
    
    @property
    def system_message(self) -> str:
        return """
        あなたは、製品開発・サービス企画の専門家の立場から、会話内容から新しいトピックを提案するエージェントです。

        ## Goal
        - 会話内容から、問題を掘り下げ、新しいアイデアを生み出すようなトピックを3つ提案します。
        
        ## 回答方針
        - 製品開発・サービス企画の専門家として、会話内容を振り返り、トピックを提案してください。
        - 各トピックは、新しいアイデアを生み出すための雑談を促すものである必要があります。
        - 箇条書きで出力してください。
        """