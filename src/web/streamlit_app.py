"""
Streamlit Chat Viewer - AIブレインストーミングチャット再現画面
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.web.cosmosdb_reader import CosmosDBReader

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
        st.session_state.current_page = 'sessions'
    if 'selected_session_id' not in st.session_state:
        st.session_state.selected_session_id = None
    if 'last_message_count' not in st.session_state:
        st.session_state.last_message_count = 0
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = 0
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 10  # デフォルト10秒

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
    
    # リフレッシュボタン
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 更新", key="refresh_sessions"):
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
    session_id = st.session_state.selected_session_id
    
    if not session_id:
        st.error("セッションが選択されていません。")
        if st.button("⬅️ セッション一覧に戻る"):
            st.session_state.current_page = 'sessions'
            st.rerun()
        return
    
    # セッション詳細を取得
    session_detail = db_reader.get_session_detail(session_id)
    if not session_detail:
        st.error("セッション情報が見つかりません。")
        if st.button("⬅️ セッション一覧に戻る"):
            st.session_state.current_page = 'sessions'
            st.rerun()
        return
    
    # ヘッダー
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ 戻る", key="back_to_sessions"):
            st.session_state.current_page = 'sessions'
            st.rerun()
    
    with col2:
        st.title(f"💬 チャット表示: {session_id}")
    
    with col3:
        # 実行中セッションの場合は自動リフレッシュオプション
        if session_detail['status'] == 'running':
            st.session_state.auto_refresh = st.checkbox("🔄 自動更新", value=st.session_state.auto_refresh)
    
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
        if st.button("📋 セッション一覧", use_container_width=True):
            st.session_state.current_page = 'sessions'
            st.rerun()
        
        if st.session_state.selected_session_id:
            if st.button("💬 チャット表示", use_container_width=True):
                st.session_state.current_page = 'chat'
                st.rerun()
        
        st.markdown("---")
        st.caption("AI Brainstorming Chat Viewer v1.0")
    
    # メインページ表示
    if st.session_state.current_page == 'sessions':
        show_sessions_page(db_reader)
    elif st.session_state.current_page == 'chat':
        show_chat_page(db_reader)

if __name__ == "__main__":
    main()