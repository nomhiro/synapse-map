# Web UIの実装

Streamlitを使ったWebUIの具体的な実装について、3つの主要画面の設計思想と実装詳細を解説します。

## 3つの画面設計の考え方

### なぜ3つの画面に分けたのか

ユーザーの使用パターンを分析した結果、以下の3つの主要なユースケースがあることが分かりました：

1. **リアルタイム実行**: 今すぐアイデアを検討したい
2. **過去振り返り**: 以前の議論を確認したい  
3. **詳細分析**: 特定のセッションを深く分析したい

これらに対応するため、「ライブ」「セッション一覧」「チャット履歴」の3画面構成としました。

## メイン画面の実装

### ナビゲーション構造

```python
def main():
    st.set_page_config(
        page_title="AIブレインストーミングシステム",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # サイドバーでページ選択
    with st.sidebar:
        st.title("🧠 AIブレインストーミング")
        
        page = st.selectbox(
            "ページを選択",
            ["🚀 ライブブレインストーミング", "📋 セッション一覧", "💬 チャット履歴"],
            key="page_selector"
        )
        
        # 現在の接続状況を表示
        show_connection_status()
    
    # 選択されたページを表示
    if page == "🚀 ライブブレインストーミング":
        show_live_brainstorming_page()
    elif page == "📋 セッション一覧":
        show_sessions_page()
    elif page == "💬 チャット履歴":
        show_chat_page()
```

### 接続状況の可視化

ユーザーにシステムの状態を分かりやすく伝えるため、接続状況を表示します：

```python
def show_connection_status():
    """システムの接続状況を表示"""
    st.subheader("システム状況")
    
    try:
        # AutoGenランナーの状態
        runner = get_runner()
        if runner.is_running:
            st.success("🤖 AIエージェント実行中")
        else:
            st.info("⏸️ 待機中")
        
        # CosmosDB接続テスト
        test_cosmosdb_connection()
        st.success("🗄️ データベース接続OK")
        
    except Exception as e:
        st.error(f"⚠️ 接続エラー: {str(e)}")
        
        # トラブルシューティングヒント
        with st.expander("トラブルシューティング"):
            st.markdown("""
            **よくある問題：**
            - 環境変数が設定されていない
            - Azure OpenAIの接続情報が間違っている
            - CosmosDBの接続文字列が無効
            
            **対処方法：**
            1. `.env`ファイルを確認
            2. Azure リソースの状態を確認
            3. ネットワーク接続を確認
            """)
```

## ライブブレインストーミング画面の詳細実装

### タスク入力とセッション開始

```python
def show_live_brainstorming_page():
    st.title("🚀 ライブブレインストーミング")
    
    # 使い方の説明
    with st.expander("💡 使い方", expanded=False):
        st.markdown("""
        1. 下のテキストエリアに検討したいアイデアや課題を入力
        2. 「ブレインストーミング開始」ボタンをクリック
        3. 5人のAIエージェントが議論を開始します
        4. 議論はリアルタイムで表示されます（約5-10分）
        """)
    
    runner = get_runner()
    
    # タスク入力UI
    task = st.text_area(
        "検討したいアイデア・課題を入力してください",
        height=120,
        placeholder="例: リモートワーク時代の新しいコミュニケーションツールのアイデア",
        help="具体的であるほど、質の高い議論が期待できます"
    )
    
    # ボタンレイアウト
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        start_button = st.button(
            "🚀 ブレインストーミング開始",
            disabled=runner.is_running or not task.strip(),
            type="primary"
        )
    
    with col2:
        if runner.is_running:
            if st.button("⏹️ 停止", type="secondary"):
                stop_session(runner)
    
    # セッション開始処理
    if start_button and task.strip():
        start_new_session(runner, task)
    
    # 進行状況表示
    if hasattr(st.session_state, 'session_running') and st.session_state.session_running:
        show_live_session_progress(runner)
```

### セッション開始処理の詳細

```python
def start_new_session(runner, task):
    """新しいブレインストーミングセッションを開始"""
    try:
        with st.spinner("AIエージェントを準備中..."):
            session_id = runner.start_session_async(task)
            
            # セッション状態の初期化
            st.session_state.current_session_id = session_id
            st.session_state.live_messages = []
            st.session_state.session_running = True
            st.session_state.start_time = datetime.now()
            
            st.success(f"✅ セッション開始: {session_id}")
            time.sleep(1)  # ユーザーに成功を視認させる
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ セッション開始エラー: {str(e)}")
        handle_session_error(e)
```

### リアルタイム進行状況の表示

```python
def show_live_session_progress(runner):
    """ライブセッションの進行状況を詳細表示"""
    
    status = runner.get_session_status()
    
    # セッション情報ヘッダー
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info(f"🤖 議論進行中... ID: {status['session_id']}")
    with col2:
        elapsed = datetime.now() - st.session_state.start_time
        st.metric("経過時間", f"{elapsed.seconds // 60}分{elapsed.seconds % 60}秒")
    with col3:
        st.metric("メッセージ数", len(st.session_state.get('live_messages', [])))
    
    # プログレス表示
    if status["is_running"]:
        # 議論の段階を推定して表示
        message_count = len(st.session_state.get('live_messages', []))
        estimated_progress = min(message_count / 15, 0.95)  # 15メッセージで95%完了と推定
        
        st.progress(estimated_progress, f"進行中... ({message_count}/約15メッセージ)")
    
    # メッセージ表示エリア
    messages_container = st.container()
    
    # 新しいメッセージの取得と表示
    new_messages = runner.get_new_messages()
    if new_messages:
        if 'live_messages' not in st.session_state:
            st.session_state.live_messages = []
        st.session_state.live_messages.extend(new_messages)
    
    # メッセージ履歴の表示
    with messages_container:
        if st.session_state.get('live_messages'):
            display_messages_with_summary(st.session_state.live_messages)
    
    # セッション完了処理
    if status["session_complete"]:
        handle_session_completion()
    
    # 自動更新（実行中のみ）
    if status["is_running"]:
        time.sleep(2)
        st.rerun()
```

## セッション一覧画面の実装

### データ取得と表示

```python
def show_sessions_page():
    st.title("📋 セッション一覧")
    
    try:
        # CosmosDBから全セッションを取得
        cosmosdb_manager = get_cosmosdb_manager()
        sessions = asyncio.run(cosmosdb_manager.get_all_sessions())
        
        if not sessions:
            st.info("まだセッションがありません。ライブブレインストーミングを開始してみましょう！")
            return
        
        # セッション検索・フィルター
        show_session_filters(sessions)
        
        # セッション一覧の表示
        display_session_list(sessions)
        
    except Exception as e:
        st.error(f"セッション取得エラー: {str(e)}")
```

### セッション検索・フィルター機能

```python
def show_session_filters(sessions):
    """セッション検索・フィルター機能"""
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input(
            "🔍 セッション検索",
            placeholder="タスク内容やセッションIDで検索...",
            key="session_search"
        )
    
    with col2:
        # 日付範囲フィルター
        date_filter = st.selectbox(
            "📅 期間",
            ["全期間", "今日", "今週", "今月"],
            key="date_filter"
        )
    
    with col3:
        # ソート順
        sort_order = st.selectbox(
            "📊 並び順",
            ["新しい順", "古い順", "メッセージ数順"],
            key="sort_order"
        )
    
    # フィルタリング処理
    filtered_sessions = apply_session_filters(sessions, search_term, date_filter, sort_order)
    
    return filtered_sessions

def apply_session_filters(sessions, search_term, date_filter, sort_order):
    """セッションのフィルタリングとソート"""
    filtered = sessions.copy()
    
    # 検索フィルター
    if search_term:
        filtered = [s for s in filtered if search_term.lower() in s.get('task', '').lower() 
                   or search_term.lower() in s.get('session_id', '').lower()]
    
    # 日付フィルター
    if date_filter != "全期間":
        now = datetime.now()
        if date_filter == "今日":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == "今週":
            cutoff = now - timedelta(days=7)
        elif date_filter == "今月":
            cutoff = now - timedelta(days=30)
        
        filtered = [s for s in filtered if 
                   datetime.fromisoformat(s.get('created_at', '1970-01-01')) >= cutoff]
    
    # ソート処理
    if sort_order == "新しい順":
        filtered.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    elif sort_order == "古い順":
        filtered.sort(key=lambda x: x.get('created_at', ''))
    elif sort_order == "メッセージ数順":
        filtered.sort(key=lambda x: x.get('message_count', 0), reverse=True)
    
    return filtered
```

### セッション一覧の表示

```python
def display_session_list(sessions):
    """セッション一覧をカード形式で表示"""
    
    st.subheader(f"セッション一覧 ({len(sessions)}件)")
    
    # ページネーション
    page_size = 10
    total_pages = (len(sessions) + page_size - 1) // page_size
    
    if total_pages > 1:
        page = st.selectbox("ページ", range(1, total_pages + 1)) - 1
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_sessions = sessions[start_idx:end_idx]
    else:
        page_sessions = sessions
    
    # セッションカードの表示
    for session in page_sessions:
        display_session_card(session)

def display_session_card(session):
    """個別セッションをカード形式で表示"""
    
    with st.container():
        st.markdown("---")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.subheader(f"📝 {session.get('task', 'タスク不明')[:50]}...")
            st.caption(f"ID: {session.get('session_id', 'Unknown')}")
        
        with col2:
            st.metric("メッセージ数", session.get('message_count', 0))
            st.caption(session.get('created_at', 'Unknown'))
        
        with col3:
            if st.button(f"詳細を見る", key=f"view_{session.get('session_id')}"):
                st.session_state.selected_session_id = session.get('session_id')
                st.session_state.page_selector = "💬 チャット履歴"
                st.rerun()
```

## チャット履歴画面の実装

### セッション詳細表示

```python
def show_chat_page():
    st.title("💬 チャット履歴")
    
    # セッション選択
    if 'selected_session_id' not in st.session_state:
        show_session_selector()
        return
    
    session_id = st.session_state.selected_session_id
    
    try:
        # セッションデータを取得
        cosmosdb_manager = get_cosmosdb_manager()
        messages = asyncio.run(cosmosdb_manager.get_session_messages(session_id))
        
        if not messages:
            st.warning("このセッションにはメッセージがありません。")
            return
        
        # セッション情報ヘッダー
        show_session_header(session_id, messages)
        
        # メッセージ表示
        display_chat_history(messages)
        
        # 分析機能
        show_session_analysis(messages)
        
    except Exception as e:
        st.error(f"チャット履歴取得エラー: {str(e)}")

def show_session_analysis(messages):
    """セッションの分析結果を表示"""
    
    with st.expander("📊 セッション分析", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # エージェント別発言回数
            agent_counts = {}
            for msg in messages:
                agent = msg.get('source', 'unknown')
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
            st.subheader("エージェント別発言数")
            for agent, count in agent_counts.items():
                st.metric(get_agent_display_name(agent), count)
        
        with col2:
            # 議論の時系列分析
            st.subheader("議論の流れ")
            timeline_data = create_timeline_data(messages)
            st.bar_chart(timeline_data)
```

このような実装により、ユーザーフレンドリーで機能豊富なWebUIを実現しています。次のセクションでは、データの永続化とCosmosDB連携について詳しく解説します。