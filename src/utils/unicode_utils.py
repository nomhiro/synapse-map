"""
Unicode Utils - Unicode文字の安全な処理
"""

import sys
from typing import Any


def safe_print(message: Any) -> None:
    """Unicode文字を安全に出力する"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Windows環境でのcp1252エンコーディングエラーを回避
        if isinstance(message, str):
            encoded_message = message.encode('utf-8', 'replace').decode('utf-8')
            print(encoded_message)
        else:
            print(str(message).encode('utf-8', 'replace').decode('utf-8'))


def safe_format_output(source: str, content_type: str, content: str) -> str:
    """出力メッセージを安全にフォーマットする"""
    try:
        return f" ------ {source} ({content_type}) ------\n{content}\n"
    except UnicodeEncodeError:
        safe_content = content.encode('utf-8', 'replace').decode('utf-8')
        return f" ------ {source} ({content_type}) ------\n{safe_content}\n"


def ensure_utf8_encoding() -> None:
    """UTF-8エンコーディングを確保する（Windows対応）"""
    if sys.platform.startswith('win'):
        # Windows環境でのUTF-8出力を改善
        import locale
        import os
        
        # 環境変数でUTF-8を指定
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        try:
            locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except locale.Error:
                # UTF-8ロケールが利用できない場合はスキップ
                pass