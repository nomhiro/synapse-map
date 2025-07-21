# コア実装の解説

エージェントシステムの心臓部である`SessionManager`と、エージェント間の協調メカニズムについて詳しく見ていきます。

## SessionManagerの役割と実装

### なぜSessionManagerが必要なのか

AutoGenのエージェントは強力ですが、単体では「会話の記録」「外部システムとの連携」「リアルタイム通知」といった機能は提供されません。SessionManagerは、これらの機能を統合的に管理する中枢的な役割を果たします。

### 核心となるメッセージフック機能

リアルタイム表示を実現する上で最も重要なのが、メッセージフック機能です：

```python
class SessionManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session_id = None
        self.message_hooks = []  # 外部通知用のフック
        self.cosmosdb_manager = None
        
    def add_message_hook(self, hook: Callable[[Dict[str, Any]], None]):
        """外部システムへの通知フックを追加"""
        self.message_hooks.append(hook)
    
    def _notify_message_hooks(self, message_data: Dict[str, Any]):
        """すべてのフックに新しいメッセージを通知"""
        for hook in self.message_hooks:
            try:
                hook(message_data)
            except Exception as e:
                safe_print(f"メッセージフック実行エラー: {e}")
```

このフック機能により、StreamlitのUIに即座にメッセージを反映できます。

### エージェント作成と会話実行

各エージェントの作成から実際の会話実行までのフローを見てみましょう：

```python
def _create_team(self) -> SelectorGroupChat:
    """5つの専門エージェントとセレクターからなるチームを作成"""
    
    # LLM設定を統一
    llm_config = {
        "config_list": [
            {
                "model": self.settings.azure_openai_model,
                "api_type": "azure",
                "api_version": self.settings.azure_openai_api_version,
                "base_url": self.settings.azure_openai_endpoint,
                "api_key": self.settings.azure_openai_api_key,
            }
        ],
        "temperature": 0.7,
    }
    
    # 各専門エージェントを作成
    agents = [
        CreativePlannerAgent().create_agent(llm_config),
        MarketAnalystAgent().create_agent(llm_config),
        TechnicalValidatorAgent().create_agent(llm_config),
        BusinessEvaluatorAgent().create_agent(llm_config),
        UserAdvocateAgent().create_agent(llm_config)
    ]
    
    # 司会者エージェントを作成
    selector = AssistantAgent(
        name="selector",
        system_message=self._create_selector_prompt(),
        llm_config=llm_config,
    )
    
    # カスタム終了条件を設定
    termination = AgentCountTermination(max_count_per_agent=3)
    
    return SelectorGroupChat(
        participants=agents,
        model_client=selector,
        termination_condition=termination,
    )
```

### 会話実行とリアルタイム処理

実際の会話実行では、各メッセージをリアルタイムで処理します：

```python
async def run_team_chat(self, team, task):
    """チームでの会話を実行し、リアルタイムで処理"""
    try:
        # ストリーミング形式で会話を開始
        stream = team.run_stream(task=task)
        
        async for chunk in stream:
            if hasattr(chunk, 'type') and chunk.type == "TextMessage":
                # メッセージデータを構造化
                message_data = {
                    "source": chunk.source,
                    "content": chunk.content,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "session_id": self.session_id
                }
                
                # 外部システムに即座に通知
                self._notify_message_hooks(message_data)
                
                # CosmosDBにリアルタイム保存
                if self.cosmosdb_manager:
                    await self.cosmosdb_manager.save_message_realtime(message_data)
                    
    except Exception as e:
        safe_print(f"チャット実行エラー: {e}")
        raise
```

## エージェント間の協調メカニズム

### SelectorGroupChatの仕組み

AutoGenのSelectorGroupChatは、動的にエージェントを選択して会話を進行します。ここで重要なのは司会者（Selector）の役割です：

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

重要な原則：
- 同じエージェントが連続で話さないように配慮
- すべてのエージェントが均等に発言機会を得られるように
- 議論の自然な流れを最優先に考える

次に発言させるエージェント名のみを回答してください。"""
```

この司会者の存在により、人間のファシリテーターのような役割をAIが担い、議論が自然に進行します。

### 終了条件の実装詳細

議論をいつ終了させるかは、システムの品質を左右する重要な要素です。シンプルな回数制限ではなく、「全員が十分に発言した時点」で終了するカスタム条件を実装しました：

```python
class AgentCountTermination(TerminationCondition):
    """各エージェントの発言回数に基づく終了条件"""
    
    def __init__(self, max_count_per_agent: int = 3):
        self._max_count = max_count_per_agent
        self._agent_message_count = {}
    
    async def __call__(self, messages) -> bool:
        if not messages:
            return False
            
        # 最新のメッセージを確認
        last_message = messages[-1]
        agent_name = last_message.source
        
        # システムメッセージやユーザーメッセージは除外
        if agent_name not in ["user", "assistant", "system", "selector"]:
            # エージェントの発言回数をカウント
            self._agent_message_count[agent_name] = \
                self._agent_message_count.get(agent_name, 0) + 1
        
        # 規定回数発言したエージェントの数を確認
        active_agents = [
            name for name, count in self._agent_message_count.items() 
            if count >= self._max_count
        ]
        
        # 5人全員が規定回数発言したら終了
        if len(active_agents) >= 5:
            return True
        
        return False
```

この実装により、全員が平等に発言し、充実した議論が保証されます。

## エラーハンドリングと安定性

### 文字エンコーディング問題への対処

AutoGenの詳細ログで日本語文字化けが発生する問題を解決するため、専用の出力関数を実装しました：

```python
def safe_print(message: str, end: str = "\n"):
    """安全な文字列出力（エンコーディングエラーを回避）"""
    try:
        print(message, end=end)
    except UnicodeEncodeError:
        # エンコーディングエラーの場合、ASCII安全な形式で出力
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(f"[エンコーディングエラー回避] {safe_message}", end=end)
```

### 接続エラーと再試行

CosmosDBへの接続が不安定な場合に備えて、再試行機能も実装しています：

```python
async def save_message_realtime(self, message_data: Dict[str, Any], max_retries: int = 3):
    """メッセージをリアルタイムで保存（リトライ機能付き）"""
    for attempt in range(max_retries):
        try:
            # ユニークIDを生成（マイクロ秒まで含めて重複回避）
            sequence = len(await self.get_session_messages()) + 1
            unique_id = f"{self.session_id}_msg_{sequence:04d}_{int(time.time() * 1000000)}"
            
            message_doc = {
                "id": unique_id,
                "session_id": self.session_id,
                "type": "message",
                "source": message_data["source"],
                "content": message_data["content"],
                "timestamp": message_data["timestamp"],
                "sequence": sequence
            }
            
            await self.container.create_item(message_doc)
            return  # 成功したら終了
            
        except Exception as e:
            if attempt == max_retries - 1:  # 最後の試行
                safe_print(f"CosmosDB保存エラー（最終試行）: {e}")
                raise
            else:
                safe_print(f"CosmosDB保存エラー（試行{attempt + 1}）: {e}")
                await asyncio.sleep(1)  # 1秒待機してリトライ
```

## 設定管理とセキュリティ

環境変数からの設定読み込みも重要な実装ポイントです：

```python
@classmethod
def from_env(cls) -> 'Settings':
    """環境変数から設定を読み込み"""
    try:
        return cls(
            azure_openai_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_openai_model=os.environ.get("AZURE_OPENAI_MODEL", "gpt-4"),
            cosmosdb_endpoint=os.environ["COSMOSDB_ENDPOINT"],
            cosmosdb_key=os.environ["COSMOSDB_KEY"],
            cosmosdb_database_name=os.environ.get("COSMOSDB_DATABASE_NAME", "brainstorming_db"),
            cosmosdb_container_name=os.environ.get("COSMOSDB_CONTAINER_NAME", "sessions")
        )
    except KeyError as e:
        raise EnvironmentError(f"必要な環境変数が設定されていません: {e}")
```

これらの実装により、堅牢で拡張性の高いマルチエージェントシステムが実現されています。次のセクションでは、このシステムをStreamlitのWebUIと統合する方法について詳しく解説します。