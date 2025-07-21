"""
Streamlit Chat Viewer - AIブレインストーミングチャット再現画面
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, List
import sys
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# プロジェクトルートをPythonパスに追加
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from cosmosdb_reader import CosmosDBReader
from autogen_runner import get_runner

# Streamlit設定
st.set_page_config(
    page_title="AI Brainstorming Chat Viewer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """セッション状態を初期化"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'live'
    if 'selected_session_id' not in st.session_state:
        st.session_state.selected_session_id = None
    if 'last_message_count' not in st.session_state:
        st.session_state.last_message_count = 0
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = 0
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 10  # デフォルト10秒
    if 'live_messages' not in st.session_state:
        st.session_state.live_messages = []
    if 'current_task' not in st.session_state:
        st.session_state.current_task = ""
    if 'session_running' not in st.session_state:
        st.session_state.session_running = False

def format_status(status: str) -> str:
    """ステータスを日本語で表示"""
    status_map = {
        'running': '🟡 実行中',
        'completed': '🟢 完了',
        'failed': '🔴 失敗',
        'unknown': '❓ 不明'
    }
    return status_map.get(status, f'❓ {status}')

def format_duration(execution_time: float) -> str:
    """実行時間を読みやすい形式に変換"""
    if execution_time <= 0:
        return "-"
    
    if execution_time < 60:
        return f"{execution_time:.1f}秒"
    elif execution_time < 3600:
        minutes = execution_time / 60
        return f"{minutes:.1f}分"
    else:
        hours = execution_time / 3600
        return f"{hours:.1f}時間"

def show_sessions_page(db_reader: CosmosDBReader):
    """セッション一覧ページを表示"""
    st.title("💬 AI Brainstorming セッション一覧")
    
    if not db_reader.is_available():
        st.error("CosmosDBが利用できません。設定を確認してください。")
        st.info("`.env`ファイルでCOSMOSDB_ENABLED=trueに設定し、接続情報を確認してください。")
        return
    
    # リフレッシュとクリアボタン
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("🔄 更新", key="refresh_sessions"):
            st.rerun()
    
    with col2:
        if st.button("🧹 画面クリア", key="clear_sessions_display", help="セッション一覧表示をクリアして再読み込みします"):
            # セッション状態をリセットしてから再読み込み
            if 'sessions_display_cleared' not in st.session_state:
                st.session_state.sessions_display_cleared = True
            st.rerun()
    
    # セッション一覧を取得
    with st.spinner("セッション一覧を読み込み中..."):
        sessions = db_reader.get_sessions(limit=50)
    
    if not sessions:
        st.warning("セッションが見つかりません。")
        return
    
    # セッション一覧を表示
    st.subheader(f"📋 セッション一覧 ({len(sessions)}件)")
    
    # セッションを一つずつ表示
    for i, session in enumerate(sessions):
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 3, 1])
            
            with col1:
                st.write(f"**{session['session_id']}**")
                st.caption(f"開始: {session['start_time']}")
            
            with col2:
                st.write(format_status(session['status']))
                messages = session.get('statistics', {}).get('total_messages', 0)
                st.caption(f"💬 {messages}件")
            
            with col3:
                task_preview = session['task'][:80] + '...' if len(session['task']) > 80 else session['task']
                st.write(task_preview)
                duration = format_duration(session.get('execution_time', 0))
                st.caption(f"⏱️ {duration}")
            
            with col4:
                if st.button("📖 開く", key=f"open_{session['session_id']}"):
                    st.session_state.selected_session_id = session['session_id']
                    st.session_state.current_page = 'chat'
                    st.rerun()
            
            st.divider()

def show_chat_page(db_reader: CosmosDBReader):
    """チャット表示ページを表示"""
    # ページが変更された際にコンテンツをクリア
    if 'page_changed' not in st.session_state:
        st.session_state.page_changed = False
    
    if st.session_state.current_page == 'chat' and not st.session_state.page_changed:
        st.session_state.page_changed = True
        # 前のページの内容をクリアするために再実行
        st.rerun()
    
    session_id = st.session_state.selected_session_id
    
    if not session_id:
        st.error("セッションが選択されていません。")
        if st.button("⬅️ セッション一覧に戻る"):
            st.session_state.current_page = 'sessions'
            st.session_state.page_changed = False
            st.rerun()
        return
    
    # セッション詳細を取得
    session_detail = db_reader.get_session_detail(session_id)
    if not session_detail:
        st.error("セッション情報が見つかりません。")
        if st.button("⬅️ セッション一覧に戻る"):
            st.session_state.current_page = 'sessions'
            st.session_state.page_changed = False
            st.rerun()
        return
    
    # ヘッダー
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ 戻る", key="back_to_sessions"):
            st.session_state.current_page = 'sessions'
            st.session_state.page_changed = False
            st.rerun()
    
    with col2:
        st.title(f"💬 チャット表示: {session_id}")
    
    with col3:
        # 実行中セッションの場合は自動リフレッシュオプション
        if session_detail['status'] == 'running':
            col3_1, col3_2 = st.columns([1, 1])
            with col3_1:
                st.session_state.auto_refresh = st.checkbox("🔄 自動更新", value=st.session_state.auto_refresh)
            with col3_2:
                if st.button("🧹 表示クリア", key="clear_chat_display", help="チャット表示をクリアして再読み込みします"):
                    chat_container.empty()
                    st.rerun()
    
    # セッション情報
    with st.expander("📊 セッション情報", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ステータス", format_status(session_detail['status']))
            st.metric("開始時刻", session_detail['start_time'])
        with col2:
            stats = session_detail.get('statistics', {})
            st.metric("メッセージ数", stats.get('total_messages', 0))
            st.metric("実行時間", format_duration(session_detail.get('execution_time', 0)))
        with col3:
            team_info = session_detail.get('team_info', {})
            st.metric("エージェント数", team_info.get('agent_count', 0))
            st.metric("最終更新", session_detail['updated_at'])
    
    # タスク情報
    st.subheader("🎯 タスク")
    st.write(session_detail['task'])
    
    # チャットメッセージを取得
    messages = db_reader.get_session_messages(session_id)
    
    # チャット表示
    st.subheader("💭 会話履歴")
    
    # 現在のメッセージ数を保存
    current_message_count = len(messages)
    
    # エージェント別のアバター設定
    agent_avatars = {
        'creative_planner': '🎨',
        'market_analyst': '📊',
        'technical_validator': '⚙️',
        'business_evaluator': '💼',
        'user_advocate': '👥',
        'system': '🤖'
    }
    
    # エージェント名を日本語に変換
    agent_names = {
        'creative_planner': 'クリエイティブプランナー',
        'market_analyst': 'マーケットアナリスト', 
        'technical_validator': 'テクニカルバリデーター',
        'business_evaluator': 'ビジネスエバリュエーター',
        'user_advocate': 'ユーザー体験専門家',
        'system': 'システム'
    }
    
    # チャットコンテナを作成（更新可能）
    chat_container = st.container()
    
    def display_messages(messages_to_show):
        """メッセージを表示する関数"""
        if not messages_to_show:
            chat_container.info("まだメッセージがありません。")
        else:
            with chat_container:
                for message in messages_to_show:
                    agent = message['source']
                    content = message['content']
                    timestamp = message['timestamp']
                    
                    agent_display = agent_names.get(agent, agent)
                    avatar = agent_avatars.get(agent, '🤖')
                    
                    # チャットメッセージコンポーネントを使用
                    with st.chat_message(agent, avatar=avatar):
                        st.markdown(f"**{agent_display}** *({timestamp})*")
                        st.markdown(content)
    
    # 初回表示
    display_messages(messages)
    
    # 実行中セッションの場合は自動リフレッシュ（部分更新）
    if session_detail['status'] == 'running' and st.session_state.auto_refresh:
        # メッセージ数の変化チェック
        if current_message_count != st.session_state.last_message_count:
            st.session_state.last_message_count = current_message_count
            # 新しいメッセージがある場合のみ表示更新
            chat_container.empty()
            display_messages(messages)
        
        # 5秒待機して再読み込み
        time.sleep(5)
        st.rerun()

def show_live_brainstorming_page():
    """ライブブレインストーミングページを表示"""
    st.title("🧠 ライブブレインストーミング")
    
    # AutoGenランナーを取得
    runner = get_runner()
    
    # 設定チェック
    if runner.settings is None:
        st.error("⚠️ 環境変数が設定されていません")
        st.info("`.env`ファイルを作成して、以下の環境変数を設定してください：")
        st.code("""
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AOAI_DEPLOYMENT_CHAT=your-chat-deployment-name
AOAI_DEPLOYMENT_REASONING=your-reasoning-deployment-name
        """)
        st.info("設定方法の詳細は [SETUP.md](SETUP.md) を参照してください。")
        return
    
    # ヘルスチェック状態を表示
    health_container = st.container()
    
    # タスク入力セクション
    st.subheader("🎯 ブレインストーミングタスク")
    
    # セッションが実行中でない場合のみタスク入力を表示
    if not st.session_state.session_running:
        task_input = st.text_area(
            "検討したいアイデア・課題を入力してください：",
            value=st.session_state.current_task,
            height=100,
            placeholder="例: 新しいフィットネスアプリのアイデア検討\n例: ECサイトのユーザー体験向上策\n例: AIを活用した教育サービス企画"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🚀 ブレインストーミング開始", type="primary", disabled=not task_input.strip()):
                if task_input.strip():
                    st.session_state.current_task = task_input.strip()
                    st.session_state.session_running = True
                    st.session_state.live_messages = []
                    
                    # セッション開始
                    try:
                        session_id = runner.start_session_async(
                            task_input.strip(),
                            callback=lambda event: _handle_session_event(event)
                        )
                        st.session_state.selected_session_id = session_id
                        st.success(f"セッション開始: {session_id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"セッション開始エラー: {e}")
        
        with col2:
            # ヘルスチェックボタン
            if st.button("🔍 システムチェック"):
                with st.spinner("システムをチェック中..."):
                    # 非同期ヘルスチェックを同期的に実行
                    import asyncio
                    try:
                        # 新しいイベントループを作成
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        is_healthy = loop.run_until_complete(runner.health_check())
                        loop.close()
                        
                        if is_healthy:
                            health_container.success("✅ システム正常")
                        else:
                            health_container.error("❌ システムエラー - 設定を確認してください")
                    except Exception as e:
                        health_container.error(f"❌ ヘルスチェックエラー: {e}")
    
    else:
        # セッション実行中の表示
        st.info(f"🏃‍♂️ 実行中のタスク: {st.session_state.current_task}")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("⏹️ セッション停止", type="secondary"):
                runner.stop_session()
                st.session_state.session_running = False
                st.session_state.current_task = ""
                st.rerun()
    
    # ライブチャット表示
    st.subheader("💭 リアルタイム会話")
    
    # 新しいメッセージを取得
    if st.session_state.session_running:
        new_messages = runner.get_new_messages()
        st.session_state.live_messages.extend(new_messages)
        
        # セッション状態を更新
        if not runner.is_session_running():
            st.session_state.session_running = False
    
    # チャットメッセージを表示
    chat_container = st.container()
    
    if not st.session_state.live_messages:
        with chat_container:
            st.info("ブレインストーミングを開始すると、ここにAIエージェントの会話がリアルタイムで表示されます。")
    else:
        # エージェント別のアバター設定
        agent_avatars = {
            'creative_planner': '🎨',
            'market_analyst': '📊',
            'technical_validator': '⚙️',
            'business_evaluator': '💼',
            'user_advocate': '👥',
            'system': '🤖'
        }
        
        # エージェント名を日本語に変換
        agent_names = {
            'creative_planner': 'クリエイティブプランナー',
            'market_analyst': 'マーケットアナリスト', 
            'technical_validator': 'テクニカルバリデーター',
            'business_evaluator': 'ビジネスエバリュエーター',
            'user_advocate': 'ユーザー体験専門家',
            'system': 'システム'
        }
        
        with chat_container:
            for message in st.session_state.live_messages:
                msg_type = message.get('type', 'message')
                
                if msg_type == 'system':
                    st.info(f"🤖 {message['content']}")
                elif msg_type == 'error':
                    st.error(f"❌ {message['content']}")
                else:
                    agent = message.get('source', 'unknown')
                    content = message.get('content', '')
                    timestamp = message.get('timestamp', '')
                    
                    agent_display = agent_names.get(agent, agent)
                    avatar = agent_avatars.get(agent, '🤖')
                    
                    # チャットメッセージコンポーネントを使用
                    with st.chat_message(agent, avatar=avatar):
                        st.markdown(f"**{agent_display}** *({timestamp[:19]})*")
                        st.markdown(content)
    
    # オンデマンド更新コントロール
    if st.session_state.session_running:
        # 自動更新か手動更新かの選択
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            auto_refresh = st.checkbox("🔄 自動更新", value=True, key="live_auto_refresh")
        
        with col2:
            if st.button("🧹 画面クリア", help="チャット表示をクリアします"):
                st.session_state.live_messages = []
                st.rerun()
        
        # 自動更新の場合
        if auto_refresh:
            time.sleep(2)  # 2秒間隔で更新
            st.rerun()
        else:
            # 手動更新ボタン
            with col3:
                if st.button("🔄 手動更新", help="新しいメッセージを取得します"):
                    st.rerun()
    else:
        # セッション停止時のクリアボタン
        if st.session_state.live_messages:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🧹 履歴クリア", help="チャット履歴をクリアします"):
                    st.session_state.live_messages = []
                    st.rerun()

def _handle_session_event(event: str):
    """セッションイベントハンドラー"""
    if event == 'session_completed':
        st.session_state.session_running = False

def main():
    """メイン関数"""
    init_session_state()
    
    # サイドバー
    with st.sidebar:
        st.title("🎛️ ナビゲーション")
        
        # CosmosDB接続状態
        db_reader = CosmosDBReader()
        if db_reader.is_available():
            st.success("✅ CosmosDB接続OK")
        else:
            st.error("❌ CosmosDB接続エラー")
        
        st.markdown("---")
        
        # ページ選択
        if st.button("🧠 ライブブレインストーミング", use_container_width=True):
            st.session_state.current_page = 'live'
            st.session_state.page_changed = False
            st.rerun()
        
        if st.button("📋 セッション一覧", use_container_width=True):
            st.session_state.current_page = 'sessions'
            st.session_state.page_changed = False
            st.rerun()
        
        if st.session_state.selected_session_id:
            if st.button("💬 チャット表示", use_container_width=True):
                st.session_state.current_page = 'chat'
                st.session_state.page_changed = False
                st.rerun()
        
        st.markdown("---")
        
        # グローバル操作
        st.subheader("🛠️ 操作")
        
        if st.button("🧹 全画面クリア", use_container_width=True, help="現在の画面表示を完全にクリアします"):
            # 主要なセッション状態をクリア
            keys_to_clear = [
                'live_messages', 'page_changed', 'sessions_display_cleared',
                'last_message_count', 'last_update_time'
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        if st.button("🔄 システム再起動", use_container_width=True, help="アプリケーション状態を完全にリセットします"):
            # 全セッション状態をクリア（選択されたセッション以外）
            preserve_keys = ['selected_session_id', 'current_page']
            preserved = {k: st.session_state.get(k) for k in preserve_keys if k in st.session_state}
            
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # 必要な状態のみ復元
            for k, v in preserved.items():
                st.session_state[k] = v
            
            st.rerun()
        
        st.markdown("---")
        st.caption("AI Brainstorming System v2.0")
    
    # メインページ表示
    if st.session_state.current_page == 'live':
        show_live_brainstorming_page()
    elif st.session_state.current_page == 'sessions':
        show_sessions_page(db_reader)
    elif st.session_state.current_page == 'chat':
        show_chat_page(db_reader)

if __name__ == "__main__":
    main()