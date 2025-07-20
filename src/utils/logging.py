"""
Logging Utils - ログ設定とユーティリティ
"""

import logging
import os
from datetime import datetime
from typing import Optional


def setup_logging(
    log_directory: str = "logs",
    log_level: str = "INFO",
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> logging.Logger:
    """ログ設定を初期化する"""
    
    # ログディレクトリの作成
    os.makedirs(log_directory, exist_ok=True)
    
    # ログレベルの設定
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # ログファイル名の生成
    log_filename = datetime.now().strftime("app_%Y%m%d.log")
    log_filepath = os.path.join(log_directory, log_filename)
    
    # ログフォーマットの設定
    formatter = logging.Formatter(log_format)
    
    # ルートロガーの設定
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # ファイルハンドラーの追加
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # コンソールハンドラーの追加
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # AutoGenフレームワークの詳細ログを抑制
    _suppress_autogen_logs()
    
    return logger


def _suppress_autogen_logs():
    """AutoGenフレームワークの詳細ログを抑制する"""
    # AutoGenの詳細なイベントログを抑制
    autogen_loggers = [
        "autogen_core.events",
        "autogen_core", 
        "httpx",
        "openai",
        "azure"
    ]
    
    for logger_name in autogen_loggers:
        autogen_logger = logging.getLogger(logger_name)
        autogen_logger.setLevel(logging.WARNING)  # WARNINGレベル以上のみ表示


def get_logger(name: str) -> logging.Logger:
    """名前付きロガーを取得する"""
    return logging.getLogger(name)


def log_performance(func_name: str, start_time: float, end_time: float) -> None:
    """パフォーマンスログを出力する"""
    logger = get_logger("performance")
    execution_time = end_time - start_time
    logger.info(f"{func_name} executed in {execution_time:.2f} seconds")


def log_api_call(endpoint: str, status_code: Optional[int] = None, response_time: Optional[float] = None) -> None:
    """API呼び出しログを出力する"""
    logger = get_logger("api")
    message = f"API call to {endpoint}"
    
    if status_code is not None:
        message += f" - Status: {status_code}"
    
    if response_time is not None:
        message += f" - Response time: {response_time:.2f}s"
    
    logger.info(message)