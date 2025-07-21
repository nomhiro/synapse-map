# システム構成とアーキテクチャ

AIブレインストーミングシステムの全体像から説明していきます。このシステムは大きく3つのコンポーネントから構成されています。

## アーキテクチャ全体像

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Web UI                      │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ ライブ実行   │  │ セッション一覧│  │ チャット履歴  │ │
│  └──────┬──────┘  └──────────────┘  └───────────────┘ │
└─────────┼───────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────┐
│         ▼        AutoGen Multi-Agent System             │
│  ┌─────────────────────────────────────────────────┐   │
│  │            SessionManager (調整役)                │   │
│  └────────────────────┬─────────────────────────────┘   │
│         ┌─────────────┼─────────────┐                   │
│         ▼             ▼             ▼                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │Creative   │  │Market    │  │Technical │    他2名    │
│  │Planner    │  │Analyst   │  │Validator │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│                    Azure CosmosDB                       │
│         (リアルタイムメッセージ保存)                     │
└─────────────────────────────────────────────────────────┘
```

## 技術スタックの選定理由

### なぜAutoGenを選んだのか

マルチエージェントシステムを実装する際、最初はLangChainも検討しました。しかし、AutoGenを選んだ理由は以下の通りです。

1. **会話フローの柔軟性**: AutoGenのSelectorGroupChatは、動的にエージェントを選択できる
2. **組み込みの会話管理**: メッセージ履歴やターン管理が最初から備わっている
3. **Microsoft製**: Azure OpenAIとの相性が良い

実際のコードで見ると、エージェントの定義がシンプルで直感的です：

```python
from autogen_agentchat.agents import AssistantAgent

creative_planner = AssistantAgent(
    name="creative_planner",
    system_message="""あなたは創造的なアイデアを生み出す専門家です。
    既存の枠にとらわれない斬新な視点から、革新的な提案を行います。""",
    llm_config={"model": "gpt-4"}
)
```

### Streamlitを選んだ理由

Web UIフレームワークとしては、FastAPI + React、Django、Gradioなども候補でした。Streamlitを選んだ決め手は：

1. **開発速度**: Pythonだけで完結し、フロントエンドの知識が不要
2. **リアルタイム更新**: `st.rerun()`で簡単に画面更新できる
3. **データサイエンティスト向け**: AIアプリケーションとの親和性が高い

ただし、Streamlitには制約もあります。特に非同期処理との相性は良くないため、工夫が必要でした（これについては後述します）。

### CosmosDBの採用理由

データストアとしては、PostgreSQL、MongoDB、Firestoreなども検討しました。CosmosDBを選んだのは：

1. **グローバル分散**: 将来的なスケールを考慮
2. **リアルタイム性能**: ミリ秒単位の書き込み遅延
3. **JSONネイティブ**: エージェントのメッセージをそのまま保存できる

## システムの動作フロー

実際にユーザーがブレインストーミングを開始してから結果を得るまでの流れを追ってみましょう。

### 1. タスク入力とセッション開始

```python
# StreamlitのUIでタスク入力
task = st.text_area("検討したいアイデア・課題を入力してください")

if st.button("🚀 ブレインストーミング開始"):
    # AutoGenランナーを使ってセッション開始
    runner = get_runner()
    session_id = runner.start_session_async(task)
```

ここでポイントなのは`start_session_async`です。Streamlitのメインスレッドをブロックしないよう、別スレッドでAutoGenセッションを実行します。

### 2. エージェント間の議論

セッションが開始されると、SessionManagerが司会役となって議論を進行します：

```python
async def run_team_chat(self, team, task):
    """チームでの会話を実行"""
    stream = team.run_stream(task=task)
    
    async for chunk in stream:
        if chunk.type == "TextMessage":
            # メッセージをリアルタイムで処理
            self.process_message(chunk)
```

各エージェントの発言は、即座にメッセージキューに追加され、UIに反映されます。

### 3. リアルタイム表示

Streamlit側では、定期的にメッセージキューをチェックして新しい発言を表示します：

```python
# 2秒ごとに画面を更新
if st.session_state.session_running:
    new_messages = runner.get_new_messages()
    st.session_state.live_messages.extend(new_messages)
    
    # メッセージを表示
    for message in st.session_state.live_messages:
        with st.chat_message(message['source']):
            st.markdown(message['content'])
    
    time.sleep(2)
    st.rerun()
```

### 4. データの永続化

各メッセージは、発言と同時にCosmosDBに保存されます：

```python
async def save_message_realtime(self, message_data):
    """メッセージをリアルタイムで保存"""
    message_doc = {
        "id": f"{self.session_id}_msg_{sequence}_{timestamp}",
        "session_id": self.session_id,
        "type": "message",
        "source": message_data["source"],
        "content": message_data["content"],
        "timestamp": message_data["timestamp"]
    }
    
    await self.container.create_item(message_doc)
```

## パフォーマンスとスケーラビリティ

### レスポンスタイムの最適化

システムの応答性を高めるため、以下の工夫をしています：

1. **非同期処理**: CosmosDBへの書き込みは非同期で実行
2. **メッセージキュー**: UIとバックエンドの処理を分離
3. **バッチ更新**: 画面更新は2秒間隔でまとめて実行

実測値では、タスク入力から最初のエージェント発言まで約3-5秒、その後は各発言間隔が2-4秒程度です。

### 同時実行の制限

現在の実装では、Streamlitのセッション管理の制約により、同一ブラウザからの同時実行は1セッションに制限されています。これは将来的にAzure Functionsに移行することで解決予定です。

## セキュリティとプライバシー

APIキーや機密情報の管理には特に注意を払っています：

```python
# 環境変数から設定を読み込み
@classmethod
def from_env(cls) -> 'Settings':
    return cls(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_api_key=os.environ["AZURE_OPENAI_API_KEY"],
        # ... 他の設定
    )
```

また、CosmosDBへの接続情報も環境変数で管理し、`.gitignore`でGit管理から除外しています。

## 今後の拡張性を考慮した設計

将来的な機能拡張を見据えて、以下の点に配慮しています：

1. **モジュラー設計**: エージェント、UI、データ層を明確に分離
2. **設定の外部化**: YAML形式で環境別設定を管理
3. **インターフェース定義**: 新しいエージェントを簡単に追加できる基底クラス

次のセクションでは、これらの設計思想に基づいた具体的な実装について詳しく見ていきます。