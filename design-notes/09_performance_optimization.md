# パフォーマンスと最適化

AIブレインストーミングシステムのレスポンス性能とユーザビリティを向上させるために実施した最適化について詳しく解説します。

## パフォーマンス課題の特定

### 初期実装での問題点

システム開発初期に以下のパフォーマンス問題が発生しました：

1. **UI更新の遅延**: エージェントの発言から表示まで5-10秒の遅延
2. **画面のちらつき**: 頻繁な再描画による視覚的な不快感
3. **メモリ使用量増加**: 長時間実行時のメモリリーク
4. **CosmosDB書き込み遅延**: 保存処理によるボトルネック

### パフォーマンス測定の実装

最適化の前に、適切な測定機能を実装しました：

```python
import time
import psutil
import threading
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PerformanceMetrics:
    """パフォーマンス測定結果"""
    timestamp: str
    memory_usage_mb: float
    message_latency_ms: float
    ui_update_time_ms: float
    database_write_time_ms: float
    active_threads: int

class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.start_times: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def start_timer(self, operation: str):
        """処理時間測定開始"""
        with self.lock:
            self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """処理時間測定終了"""
        with self.lock:
            if operation in self.start_times:
                elapsed = (time.time() - self.start_times[operation]) * 1000
                del self.start_times[operation]
                return elapsed
            return 0.0
    
    def record_metrics(self, message_latency: float = 0, ui_update_time: float = 0, 
                      db_write_time: float = 0):
        """メトリクスを記録"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            thread_count = threading.active_count()
            
            metric = PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                memory_usage_mb=round(memory_mb, 2),
                message_latency_ms=round(message_latency, 2),
                ui_update_time_ms=round(ui_update_time, 2),
                database_write_time_ms=round(db_write_time, 2),
                active_threads=thread_count
            )
            
            with self.lock:
                self.metrics.append(metric)
                # 古いメトリクスを削除（最新100件のみ保持）
                if len(self.metrics) > 100:
                    self.metrics = self.metrics[-100:]
                    
        except Exception as e:
            safe_print(f"メトリクス記録エラー: {e}")
    
    def get_performance_summary(self) -> Dict[str, float]:
        """パフォーマンス要約を取得"""
        if not self.metrics:
            return {}
        
        recent_metrics = self.metrics[-20:]  # 最新20件
        
        return {
            "avg_memory_mb": sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics),
            "avg_message_latency_ms": sum(m.message_latency_ms for m in recent_metrics) / len(recent_metrics),
            "avg_ui_update_ms": sum(m.ui_update_time_ms for m in recent_metrics) / len(recent_metrics),
            "avg_db_write_ms": sum(m.database_write_time_ms for m in recent_metrics) / len(recent_metrics),
            "max_threads": max(m.active_threads for m in recent_metrics)
        }

# グローバルモニターインスタンス
performance_monitor = PerformanceMonitor()
```

## メッセージ更新の最適化

### 問題: 頻繁な全体再描画

初期実装では、新しいメッセージが到着するたびに画面全体を再描画していました：

```python
# 問題のあった実装
def show_messages_slow():
    # 毎回全メッセージを再描画（非効率）
    for message in st.session_state.live_messages:
        with st.chat_message(message['source']):
            st.markdown(message['content'])
    
    # 2秒ごとに全体を更新
    time.sleep(2)
    st.rerun()
```

### 解決策: 差分更新システム

差分のみを更新する仕組みを実装しました：

```python
class OptimizedMessageDisplay:
    """最適化されたメッセージ表示クラス"""
    
    def __init__(self):
        self.last_display_count = 0
        self.message_containers = {}
        
    def update_messages_efficiently(self, messages: List[Dict[str, Any]]):
        """効率的なメッセージ更新"""
        performance_monitor.start_timer("ui_update")
        
        try:
            current_count = len(messages)
            
            # 新しいメッセージのみを処理
            if current_count > self.last_display_count:
                new_messages = messages[self.last_display_count:]
                
                # 新しいメッセージのみを表示
                for i, message in enumerate(new_messages):
                    message_index = self.last_display_count + i
                    self._display_single_message(message, message_index)
                
                self.last_display_count = current_count
            
        finally:
            ui_time = performance_monitor.end_timer("ui_update")
            performance_monitor.record_metrics(ui_update_time=ui_time)
    
    def _display_single_message(self, message: Dict[str, Any], index: int):
        """単一メッセージの表示"""
        source = message.get('source', 'unknown')
        content = message.get('content', '')
        timestamp = message.get('timestamp', '')
        
        # エージェント設定
        agent_config = self._get_agent_config(source)
        
        # コンテナを作成してキャッシュ
        container_key = f"msg_{index}"
        if container_key not in self.message_containers:
            self.message_containers[container_key] = st.container()
        
        with self.message_containers[container_key]:
            with st.chat_message(source, avatar=agent_config["icon"]):
                # タイムスタンプとエージェント名
                st.caption(f"{agent_config['name']} - {timestamp}")
                
                # メッセージ内容（マークダウン形式）
                if message.get("type") == "error":
                    st.error(content)
                else:
                    st.markdown(content)
    
    def _get_agent_config(self, source: str) -> Dict[str, str]:
        """エージェント設定を取得"""
        configs = {
            "creative_planner": {"icon": "🎨", "name": "創造的企画者"},
            "market_analyst": {"icon": "📊", "name": "市場分析者"},
            "technical_validator": {"icon": "⚙️", "name": "技術検証者"},
            "business_evaluator": {"icon": "💼", "name": "事業評価者"},
            "user_advocate": {"icon": "👥", "name": "ユーザー代弁者"},
            "system": {"icon": "🔧", "name": "システム"}
        }
        return configs.get(source, {"icon": "🤖", "name": source})

# 使用例
message_display = OptimizedMessageDisplay()

def show_live_session_optimized(runner):
    """最適化されたライブセッション表示"""
    # 新しいメッセージを取得
    new_messages = runner.get_new_messages()
    
    if new_messages:
        # セッション状態に追加
        if 'live_messages' not in st.session_state:
            st.session_state.live_messages = []
        st.session_state.live_messages.extend(new_messages)
    
    # 効率的な表示更新
    if st.session_state.get('live_messages'):
        message_display.update_messages_efficiently(st.session_state.live_messages)
```

## データベース書き込みの最適化

### 問題: 同期書き込みによるブロッキング

初期実装では、メッセージ保存が同期的に実行され、UIがブロックされていました。

### 解決策: 非同期バッファリングシステム

```python
import asyncio
import queue
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

class AsyncDatabaseWriter:
    """非同期データベース書き込みクラス"""
    
    def __init__(self, cosmosdb_manager):
        self.cosmosdb_manager = cosmosdb_manager
        self.write_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.is_running = False
        self.writer_thread = None
        
    def start_background_writer(self):
        """バックグラウンド書き込みを開始"""
        if self.is_running:
            return
            
        self.is_running = True
        self.writer_thread = threading.Thread(
            target=self._background_writer_loop,
            daemon=True
        )
        self.writer_thread.start()
        safe_print("バックグラウンドライター開始")
    
    def queue_write(self, message_data: Dict[str, Any]) -> bool:
        """書き込みをキューに追加（ノンブロッキング）"""
        try:
            self.write_queue.put_nowait(message_data)
            return True
        except queue.Full:
            safe_print("警告: 書き込みキューが満杯です")
            return False
    
    def _background_writer_loop(self):
        """バックグラウンド書き込みループ"""
        batch = []
        batch_size = 5
        timeout = 2.0  # 2秒でタイムアウト
        
        while self.is_running:
            try:
                # キューからメッセージを取得（タイムアウト付き）
                message = self.write_queue.get(timeout=timeout)
                batch.append(message)
                
                # バッチサイズに達したか、キューが空になったら書き込み
                if len(batch) >= batch_size or self.write_queue.empty():
                    self._write_batch(batch)
                    batch.clear()
                    
            except queue.Empty:
                # タイムアウト時も蓄積分を書き込み
                if batch:
                    self._write_batch(batch)
                    batch.clear()
                    
            except Exception as e:
                safe_print(f"バックグラウンド書き込みエラー: {e}")
    
    def _write_batch(self, messages: List[Dict[str, Any]]):
        """バッチ書き込み実行"""
        if not messages:
            return
            
        performance_monitor.start_timer("db_write")
        
        try:
            # 非同期書き込みを同期実行
            asyncio.run(self._async_write_batch(messages))
            safe_print(f"バッチ書き込み完了: {len(messages)}件")
            
        except Exception as e:
            safe_print(f"バッチ書き込みエラー: {e}")
            # エラー時は個別書き込みにフォールバック
            self._fallback_individual_writes(messages)
            
        finally:
            db_time = performance_monitor.end_timer("db_write")
            performance_monitor.record_metrics(db_write_time=db_time)
    
    async def _async_write_batch(self, messages: List[Dict[str, Any]]):
        """非同期バッチ書き込み"""
        tasks = []
        for message in messages:
            task = self.cosmosdb_manager.save_message_realtime(message)
            tasks.append(task)
        
        # 並列実行
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def _fallback_individual_writes(self, messages: List[Dict[str, Any]]):
        """フォールバック: 個別書き込み"""
        for message in messages:
            try:
                asyncio.run(self.cosmosdb_manager.save_message_realtime(message))
            except Exception as e:
                safe_print(f"個別書き込みエラー: {e}")
    
    def stop(self):
        """書き込み停止"""
        self.is_running = False
        
        # 残りのメッセージを処理
        remaining_messages = []
        while not self.write_queue.empty():
            try:
                remaining_messages.append(self.write_queue.get_nowait())
            except queue.Empty:
                break
        
        if remaining_messages:
            self._write_batch(remaining_messages)
        
        safe_print("バックグラウンドライター停止")
```

## メモリ使用量の最適化

### 問題: メッセージ履歴の蓄積

長時間のセッションでメッセージが蓄積し、メモリ使用量が増加する問題がありました。

### 解決策: 循環バッファとガベージコレクション

```python
import gc
import weakref
from collections import deque

class MemoryOptimizedMessageStore:
    """メモリ最適化されたメッセージストア"""
    
    def __init__(self, max_messages: int = 1000):
        self.max_messages = max_messages
        self.messages = deque(maxlen=max_messages)  # 循環バッファ
        self.weak_references = weakref.WeakSet()
        self.memory_threshold_mb = 500  # メモリ閾値
        
    def add_message(self, message: Dict[str, Any]):
        """メッセージを追加（メモリ効率を考慮）"""
        # 大きなコンテンツは要約
        if len(message.get('content', '')) > 10000:
            message = self._summarize_large_message(message)
        
        self.messages.append(message)
        
        # 定期的にメモリチェック
        if len(self.messages) % 50 == 0:
            self._check_memory_usage()
    
    def get_recent_messages(self, count: int = 50) -> List[Dict[str, Any]]:
        """最新のメッセージを取得"""
        return list(self.messages)[-count:]
    
    def get_all_messages(self) -> List[Dict[str, Any]]:
        """全メッセージを取得"""
        return list(self.messages)
    
    def _summarize_large_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """大きなメッセージを要約"""
        content = message.get('content', '')
        if len(content) > 10000:
            # 最初の1000文字 + 最後の500文字
            summarized = content[:1000] + "\n\n[... 中略 ...]\n\n" + content[-500:]
            message = message.copy()
            message['content'] = summarized
            message['original_length'] = len(content)
        return message
    
    def _check_memory_usage(self):
        """メモリ使用量をチェックし、必要に応じてクリーンアップ"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.memory_threshold_mb:
                safe_print(f"高メモリ使用量検出: {memory_mb:.1f}MB")
                self._cleanup_memory()
                
        except Exception as e:
            safe_print(f"メモリチェックエラー: {e}")
    
    def _cleanup_memory(self):
        """メモリクリーンアップを実行"""
        # 古いメッセージを削除
        if len(self.messages) > self.max_messages // 2:
            # 半分のメッセージを保持
            keep_count = self.max_messages // 2
            self.messages = deque(list(self.messages)[-keep_count:], maxlen=self.max_messages)
        
        # 明示的にガベージコレクション実行
        gc.collect()
        
        # 弱参照のクリーンアップ
        self.weak_references.clear()
        
        safe_print("メモリクリーンアップ完了")

# Streamlitセッション状態での使用
def get_optimized_message_store():
    """最適化されたメッセージストアを取得"""
    if 'message_store' not in st.session_state:
        st.session_state.message_store = MemoryOptimizedMessageStore()
    return st.session_state.message_store
```

## UI応答性の向上

### プログレス表示の改善

```python
def show_enhanced_progress(runner, messages):
    """強化されたプログレス表示"""
    status = runner.get_session_status()
    
    if status["is_running"]:
        # 動的プログレス計算
        message_count = len(messages)
        estimated_total = 15  # 予想総メッセージ数
        progress = min(message_count / estimated_total, 0.95)
        
        # エージェント別進行状況
        agent_progress = calculate_agent_progress(messages)
        
        # メインプログレスバー
        st.progress(progress, f"議論進行中... ({message_count}/{estimated_total})")
        
        # エージェント別プログレス
        col1, col2, col3, col4, col5 = st.columns(5)
        agent_names = ["創造的企画者", "市場分析者", "技術検証者", "事業評価者", "ユーザー代弁者"]
        
        for i, (col, name) in enumerate(zip([col1, col2, col3, col4, col5], agent_names)):
            with col:
                agent_count = agent_progress.get(list(agent_progress.keys())[i] if i < len(agent_progress) else "", 0)
                st.metric(name, f"{agent_count}/3")
    
    # パフォーマンス情報（デバッグ時）
    if st.sidebar.checkbox("パフォーマンス情報表示"):
        show_performance_metrics()

def calculate_agent_progress(messages):
    """エージェント別の進行状況を計算"""
    agent_counts = {}
    for message in messages:
        source = message.get('source', '')
        if source not in ['user', 'system', 'selector']:
            agent_counts[source] = agent_counts.get(source, 0) + 1
    return agent_counts

def show_performance_metrics():
    """パフォーマンスメトリクスを表示"""
    summary = performance_monitor.get_performance_summary()
    
    if summary:
        st.sidebar.subheader("📊 パフォーマンス")
        st.sidebar.metric("メモリ使用量", f"{summary.get('avg_memory_mb', 0):.1f} MB")
        st.sidebar.metric("平均レスポンス", f"{summary.get('avg_message_latency_ms', 0):.0f} ms")
        st.sidebar.metric("UI更新時間", f"{summary.get('avg_ui_update_ms', 0):.0f} ms")
        st.sidebar.metric("DB書き込み", f"{summary.get('avg_db_write_ms', 0):.0f} ms")
```

これらの最適化により、システムの応答性とユーザビリティが大幅に向上しました。次のセクションでは、今後の展望について詳しく説明します。