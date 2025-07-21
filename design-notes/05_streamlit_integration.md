# StreamlitとAutoGenの統合

AutoGenのマルチエージェントシステムをStreamlitのWebUIと統合する際に直面した技術的課題と、その解決方法について詳しく解説します。

## 統合時の主要な課題

### 1. 非同期処理とStreamlitの相性問題

Streamlitは基本的に同期的な処理モデルで設計されており、AutoGenの非同期処理と直接組み合わせるのは困難でした。AutoGenのセッションが実行中にStreamlitのメインスレッドがブロックされると、UIが応答しなくなってしまいます。

### 2. リアルタイム更新の実現

議論の進行をリアルタイムで表示するには、バックグラウンドで進行するAutoGenセッションの状況を、StreamlitのUIに反映する仕組みが必要でした。

### 3. 状態管理の複雑さ

複数のページ間での状態共有、セッションの開始・停止制御、エラーハンドリングなど、Webアプリケーションとしての堅牢性が求められました。

## StreamlitAutoGenRunnerの設計

これらの課題を解決するため、専用のアダプタークラス`StreamlitAutoGenRunner`を実装しました。

### 基本構造

```python
import threading
import queue
from typing import Dict, Any, List, Optional, Callable

class StreamlitAutoGenRunner:
    def __init__(self):
        self.session_manager = None
        self.message_queue = queue.Queue()
        self.session_thread = None
        self.is_running = False
        self.current_session_id = None
        self.session_complete = False
        
    def _message_hook(self, message_data: Dict[str, Any]):
        """SessionManagerからのメッセージを受信してキューに追加"""
        self.message_queue.put(message_data)
```

キューを使うことで、スレッド間でのメッセージ受け渡しを安全に行えます。

### 非同期セッション実行

AutoGenセッションを別スレッドで実行し、メインスレッドをブロックしない仕組みを実装しました：

```python
def start_session_async(self, task: str, callback: Optional[Callable] = None) -> str:
    """AutoGenセッションを非同期で開始"""
    if self.is_running:
        raise RuntimeError("セッションは既に実行中です")
    
    # セッションIDを生成
    self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    self.is_running = True
    self.session_complete = False
    
    # 別スレッドでセッションを実行
    self.session_thread = threading.Thread(
        target=self._run_session_in_thread,
        args=(task, callback),
        daemon=True  # メインプロセス終了時に自動的に終了
    )
    self.session_thread.start()
    
    return self.current_session_id

def _run_session_in_thread(self, task: str, callback: Optional[Callable] = None):
    """スレッド内でAutoGenセッションを実行"""
    try:
        # 設定読み込み
        settings = Settings.from_env()
        
        # SessionManagerを作成してフックを追加
        self.session_manager = SessionManager(settings)
        self.session_manager.add_message_hook(self._message_hook)
        
        # セッション実行（非同期）
        asyncio.run(self.session_manager.run_chat_session(
            session_id=self.current_session_id,
            task=task
        ))
        
        # 完了通知
        self.session_complete = True
        if callback:
            callback()
            
    except Exception as e:
        # エラー情報をキューに送信
        error_message = {
            "source": "system",
            "content": f"エラーが発生しました: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "error"
        }
        self.message_queue.put(error_message)
        
    finally:
        self.is_running = False
```

### メッセージ取得とバッファリング

UIに表示するメッセージを効率的に取得する仕組みを実装しました：

```python
def get_new_messages(self) -> List[Dict[str, Any]]:
    """新しいメッセージを全て取得（ノンブロッキング）"""
    messages = []
    
    try:
        # キューから利用可能なメッセージを全て取得
        while True:
            message = self.message_queue.get_nowait()
            messages.append(message)
    except queue.Empty:
        # キューが空になったら終了
        pass
    
    return messages

def get_session_status(self) -> Dict[str, Any]:
    """現在のセッション状況を取得"""
    return {
        "is_running": self.is_running,
        "session_id": self.current_session_id,
        "session_complete": self.session_complete,
        "queue_size": self.message_queue.qsize()
    }
```

## StreamlitUIでの統合実装

### リアルタイム更新のメインループ

Streamlitでリアルタイム更新を実現するため、以下のパターンを採用しました：

```python
def show_live_brainstorming_page():
    st.title("🚀 ライブブレインストーミング")
    
    # AutoGenランナーの初期化
    if 'runner' not in st.session_state:
        st.session_state.runner = get_runner()
    
    runner = st.session_state.runner
    
    # タスク入力UI
    task = st.text_area(
        "検討したいアイデア・課題を入力してください",
        height=100,
        placeholder="例: リモートワーク時代の新しいコミュニケーションツール"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚀 ブレインストーミング開始", disabled=runner.is_running):
            if task.strip():
                try:
                    # セッション開始
                    session_id = runner.start_session_async(task)
                    st.session_state.current_session_id = session_id
                    st.session_state.live_messages = []
                    st.session_state.session_running = True
                    st.rerun()
                except Exception as e:
                    st.error(f"セッション開始エラー: {e}")
    
    # リアルタイム表示部分
    if hasattr(st.session_state, 'session_running') and st.session_state.session_running:
        show_live_session_progress(runner)
```

### ライブセッション表示の実装

```python
def show_live_session_progress(runner):
    """ライブセッションの進行状況を表示"""
    
    # セッション状況の表示
    status = runner.get_session_status()
    
    if status["is_running"]:
        st.info(f"🤖 AIエージェントが議論中... (セッションID: {status['session_id']})")
        
        # プログレスバー（視覚的なフィードバック）
        progress_placeholder = st.empty()
        with progress_placeholder:
            st.progress(0.5, "議論進行中...")
    
    # メッセージ表示エリア
    messages_container = st.container()
    
    # 新しいメッセージを取得
    new_messages = runner.get_new_messages()
    if new_messages:
        # セッション状態に追加
        if 'live_messages' not in st.session_state:
            st.session_state.live_messages = []
        st.session_state.live_messages.extend(new_messages)
    
    # メッセージ履歴を表示
    with messages_container:
        if hasattr(st.session_state, 'live_messages'):
            for message in st.session_state.live_messages:
                display_message(message)
    
    # セッション完了チェック
    if status["session_complete"]:
        st.session_state.session_running = False
        st.success("✅ ブレインストーミングが完了しました！")
        
        # 結果保存の選択肢を提供
        if st.button("📋 結果をセッション履歴に保存"):
            save_session_to_history(st.session_state.live_messages)
            st.success("結果を保存しました")
    
    # 自動更新（2秒間隔）
    if status["is_running"]:
        time.sleep(2)
        st.rerun()
```

### メッセージ表示の工夫

各エージェントのメッセージを分かりやすく表示するため、専用の表示関数を実装しました：

```python
def display_message(message: Dict[str, Any]):
    """メッセージを適切な形式で表示"""
    
    # エージェント別のアイコンと色分け
    agent_config = {
        "creative_planner": {"icon": "🎨", "name": "創造的企画者"},
        "market_analyst": {"icon": "📊", "name": "市場分析者"},
        "technical_validator": {"icon": "⚙️", "name": "技術検証者"},
        "business_evaluator": {"icon": "💼", "name": "事業評価者"},
        "user_advocate": {"icon": "👥", "name": "ユーザー代弁者"},
        "system": {"icon": "🔧", "name": "システム"}
    }
    
    source = message.get("source", "unknown")
    config = agent_config.get(source, {"icon": "🤖", "name": source})
    
    # チャットメッセージとして表示
    with st.chat_message(source, avatar=config["icon"]):
        # エージェント名とタイムスタンプ
        st.caption(f"{config['name']} - {message.get('timestamp', '')}")
        
        # メッセージ内容
        content = message.get("content", "")
        if message.get("type") == "error":
            st.error(content)
        else:
            st.markdown(content)
```

## 状態管理とページ間連携

### セッション状態の管理

Streamlitの`session_state`を使って、ページ間でのデータ共有を実現しました：

```python
def get_runner():
    """グローバルなAutoGenランナーインスタンスを取得"""
    if 'global_runner' not in st.session_state:
        st.session_state.global_runner = StreamlitAutoGenRunner()
    return st.session_state.global_runner

def save_session_to_history(messages: List[Dict[str, Any]]):
    """セッション履歴に保存"""
    if 'session_history' not in st.session_state:
        st.session_state.session_history = []
    
    session_data = {
        "session_id": st.session_state.current_session_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": messages.copy(),
        "task": messages[0].get("content", "") if messages else ""
    }
    
    st.session_state.session_history.append(session_data)
```

### エラーハンドリングとユーザビリティ

```python
def handle_session_error(error: Exception):
    """セッションエラーの統一ハンドリング"""
    st.error(f"エラーが発生しました: {str(error)}")
    
    # デバッグ情報の表示（開発時）
    if st.secrets.get("debug_mode", False):
        st.exception(error)
    
    # セッション状態のリセット
    if 'session_running' in st.session_state:
        st.session_state.session_running = False
    
    # 復旧のための選択肢を提供
    if st.button("🔄 システムをリセット"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
```

## パフォーマンス最適化

### 画面更新の最適化

頻繁な画面更新による「ちらつき」を軽減するため、以下の工夫をしました：

```python
# メッセージ表示の差分更新
def update_messages_efficiently(new_messages: List[Dict]):
    """効率的なメッセージ更新"""
    if not new_messages:
        return
    
    # 前回の表示から変更があった場合のみ更新
    current_count = len(st.session_state.get('live_messages', []))
    
    if len(new_messages) > 0:
        # 新しいメッセージのみを追加表示
        for i, message in enumerate(new_messages):
            display_message_at_position(message, current_count + i)
```

この統合実装により、AutoGenの強力なマルチエージェント機能を、直感的で使いやすいWebUIで利用できるようになりました。次のセクションでは、WebUIの具体的な画面構成について詳しく見ていきます。