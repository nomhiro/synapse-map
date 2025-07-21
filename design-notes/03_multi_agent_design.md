# マルチエージェントシステムの設計と実装

5人の専門家による議論をAIで再現する。これがこのシステムの核心部分です。人間のブレインストーミングをモデルに、それぞれ異なる専門性を持つエージェントを設計しました。

## エージェントの役割設計

### なぜ5つのエージェントなのか

最初は3つのエージェント（技術・ビジネス・ユーザー）で始めましたが、議論が表面的になりがちでした。試行錯誤の結果、以下の5つの役割に落ち着きました：

1. **CreativePlanner（創造的企画者）**: アイデアの種を生み出す
2. **MarketAnalyst（市場分析者）**: 市場性と競合を分析
3. **TechnicalValidator（技術検証者）**: 実現可能性を検証
4. **BusinessEvaluator（事業評価者）**: ビジネス価値を評価
5. **UserAdvocate（ユーザー代弁者）**: ユーザー視点で検証

この5つの組み合わせが、最もバランスの取れた議論を生み出すことが分かりました。

## エージェントの実装

### 基底クラスの設計

まず、すべてのエージェントが継承する基底クラスを作成しました：

```python
from abc import ABC, abstractmethod
from autogen_agentchat.agents import AssistantAgent

class BaseAgent(ABC):
    """エージェントの基底クラス"""
    
    @abstractmethod
    def get_name(self) -> str:
        """エージェント名を取得"""
        pass
    
    @abstractmethod
    def get_system_message(self) -> str:
        """システムメッセージを取得"""
        pass
    
    def create_agent(self, llm_config: dict) -> AssistantAgent:
        """AutoGenエージェントを作成"""
        return AssistantAgent(
            name=self.get_name(),
            system_message=self.get_system_message(),
            llm_config=llm_config
        )
```

この設計により、新しいエージェントの追加が簡単になります。

### CreativePlannerの実装例

最も重要なCreativePlannerの実装を見てみましょう：

```python
class CreativePlannerAgent(BaseAgent):
    """創造的な企画者エージェント"""
    
    def get_name(self) -> str:
        return "creative_planner"
    
    def get_system_message(self) -> str:
        return """あなたは創造的なアイデアを生み出す専門家です。

役割：
- 既存の枠にとらわれない斬新な視点から提案を行う
- 異分野の知識を組み合わせて新しいコンセプトを創出する
- 「もし〜だったら」という仮説思考を活用する

アプローチ：
1. まず与えられた課題の本質を別の角度から捉え直す
2. 類似の成功事例を異業種から探し、応用可能性を検討する
3. 技術的制約を一旦無視して理想的なソリューションを描く
4. ユーザーの潜在的なニーズを想像力を使って掘り下げる

重要：
- 実現可能性よりもインパクトと新規性を重視する
- 他のエージェントの意見に刺激を受けて、さらに発展させる
- 「できない理由」ではなく「できる方法」を考える"""
```

システムメッセージの工夫点：
1. **明確な役割定義**: 何をすべきかが具体的
2. **アプローチの指針**: どのように考えるべきかを示す
3. **他エージェントとの協調**: 議論を発展させることを促す

## SelectorGroupChatによる議論の実現

### なぜSelectorGroupChatを使うのか

AutoGenには複数の会話パターンがありますが、SelectorGroupChatを選んだ理由は「動的な発言順序」です。

通常のRoundRobinでは発言順が固定されますが、実際のブレインストーミングでは、話の流れに応じて次の発言者が決まります。SelectorGroupChatはこれを再現できます。

### Selectorの実装

議論の司会者となるSelectorの設定が重要です：

```python
def _create_selector_prompt(self) -> str:
    return """あなたは議論の司会者です。
    
現在の議論状況を分析し、次に発言すべき最適なエージェントを選択してください。

選択の指針：
1. アイデア出しの初期段階
   → creative_planner（新しいアイデアが必要）
   
2. アイデアが出された直後
   → market_analyst（市場性の検証）
   → technical_validator（技術的実現性）
   
3. 基本的な検証が済んだ後
   → business_evaluator（ビジネス価値）
   → user_advocate（ユーザー視点）
   
4. 議論が煮詰まったとき
   → creative_planner（新しい切り口）

重要：
- 同じエージェントが連続で話さないように配慮
- すべてのエージェントが均等に発言機会を得られるように
- 議論の自然な流れを重視"""
```

この司会者の存在により、人間のファシリテーターのような役割をAIが担います。

## 終了条件の設計

### カスタム終了条件の実装

議論をいつ終了させるかは重要な問題です。単純な回数制限では、良い議論が途中で切れてしまうことがあります。

そこで、カスタムの終了条件を実装しました：

```python
class AgentCountTermination(TerminationCondition):
    """各エージェントの発言回数に基づく終了条件"""
    
    def __init__(self, max_count_per_agent: int = 3):
        self._max_count = max_count_per_agent
        self._agent_message_count = {}
    
    async def __call__(self, messages) -> bool:
        # 最新のメッセージを確認
        if messages:
            last_message = messages[-1]
            agent_name = last_message.source
            
            # システムメッセージは除外
            if agent_name not in ["user", "assistant", "system"]:
                self._agent_message_count[agent_name] = \
                    self._agent_message_count.get(agent_name, 0) + 1
            
            # すべてのエージェントが規定回数発言したら終了
            active_agents = [name for name, count in self._agent_message_count.items() 
                           if count >= self._max_count]
            
            if len(active_agents) >= 5:  # 5人全員が発言
                return True
        
        return False
```

この実装により、全員が十分に発言した時点で自然に議論が終了します。

## 実際の議論例

これらの設計がどのように機能するか、実際の議論例を見てみましょう：

```
タスク: 「リモートワーク時代の新しいコミュニケーションツール」

creative_planner: 「物理的な距離を感じさせない『空間共有型』のツールを提案します。
VRではなく、デスクトップ上に仮想オフィスを再現し、アバターが自然に動き回れる
2.5次元の空間です。雑談や偶発的な出会いを演出できます」

market_analyst: 「Gather.townやSpatialChatなど類似サービスは存在しますが、
日本市場での認知度はまだ低いです。特に日本企業の文化に合わせた
『席次』や『会議室予約』機能があれば差別化できるでしょう」

technical_validator: 「WebRTCとCanvas APIを使えば、ブラウザだけで実装可能です。
重要なのは低遅延での同期です。まずは10人規模から始めて、
段階的にスケールアップする approach が現実的でしょう」

business_evaluator: 「SaaSモデルで1ユーザー月額1,000円なら、
100社×20人で月商200万円。開発費用を考慮すると、
18ヶ月でブレークイーブンが見込めます」

user_advocate: 「リモートワークの最大の課題は『孤独感』です。
このツールが単なる会議ツールではなく、『つながり』を感じられる
場所になることが成功の鍵ですね」
```

各エージェントが前の発言を受けて、自分の専門性から付加価値を加えているのが分かります。

## エージェント設計のポイント

### 1. 専門性の明確化

各エージェントの専門領域を明確にし、重複を避けることが重要です。曖昧な役割定義は、議論の質を下げる原因になります。

### 2. 協調性の組み込み

システムメッセージに「他のエージェントの意見を踏まえて」という指示を含めることで、議論が発展しやすくなります。

### 3. バランスの考慮

批判的すぎるエージェントがいると議論が停滞し、楽観的すぎると現実味がなくなります。このバランスを取ることが、良い議論を生む秘訣です。

## 課題と今後の改善点

現在のシステムにもいくつか課題があります：

1. **文脈の長期記憶**: 議論が長くなると、初期の重要な発言を忘れがち
2. **専門知識の深さ**: より専門的な議論には、ドメイン特化のエージェントが必要
3. **感情的側面**: 人間のブレインストーミングにある「盛り上がり」の再現

これらは今後のバージョンアップで対応していく予定です。

次のセクションでは、これらのエージェントをどのようにStreamlitと統合したか、技術的な詳細を説明します。