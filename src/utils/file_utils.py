"""
File Utils - ファイル操作ユーティリティ
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


def format_timestamp(dt: datetime = None) -> str:
    """統一されたタイムスタンプ形式を返す"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # ミリ秒まで


def create_logs_dir(log_directory: str = "logs") -> None:
    """ログディレクトリを作成する"""
    Path(log_directory).mkdir(parents=True, exist_ok=True)


def save_context(chat_contexts: List[Dict[str, Any]], log_directory: str = "logs") -> str:
    """チャットコンテキストをJSONファイルに保存する"""
    create_logs_dir(log_directory)
    
    filename = datetime.now().strftime("context_%Y%m%d_%H%M%S.json")
    filepath = os.path.join(log_directory, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(chat_contexts, f, ensure_ascii=False, indent=2, default=str)
    
    return filename


def load_context(filename: str, log_directory: str = "logs") -> List[Dict[str, Any]]:
    """JSONファイルからチャットコンテキストを読み込む"""
    filepath = os.path.join(log_directory, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Context file not found: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_context_files(log_directory: str = "logs") -> List[str]:
    """ログディレクトリ内のコンテキストファイル一覧を取得"""
    if not os.path.exists(log_directory):
        return []
    
    files = [f for f in os.listdir(log_directory) if f.startswith("context_") and f.endswith(".json")]
    return sorted(files, reverse=True)  # 新しいファイルが先頭に来るように


def cleanup_old_contexts(log_directory: str = "logs", keep_count: int = 10) -> None:
    """古いコンテキストファイルを削除する"""
    context_files = list_context_files(log_directory)
    
    if len(context_files) <= keep_count:
        return
    
    files_to_delete = context_files[keep_count:]
    for filename in files_to_delete:
        filepath = os.path.join(log_directory, filename)
        try:
            os.remove(filepath)
            print(f"Removed old context file: {filename}")
        except OSError as e:
            print(f"Error removing file {filename}: {e}")