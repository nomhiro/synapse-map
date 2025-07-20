"""
Main - メインエントリポイント
"""

import asyncio
import argparse
import sys
import os
from dotenv import load_dotenv
from typing import Optional

# 直接実行時の絶対インポート
from config.settings import Settings
from core.session_manager import SessionManager
from utils.logging import setup_logging
from utils.unicode_utils import ensure_utf8_encoding

# プロジェクトルートをPythonパスに追加（直接実行時）
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)



def parse_arguments():
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description="AI Brainstorming System")
    
    parser.add_argument(
        "--task",
        type=str,
        help="Custom task for brainstorming session"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode to input task"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        choices=["development", "production"],
        default="development",
        help="Configuration environment"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override log level"
    )
    
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health check and exit"
    )
    
    return parser.parse_args()


async def main():
    """メイン実行関数"""
    # Unicode エンコーディングの設定
    ensure_utf8_encoding()
    
    # 環境変数の読み込み
    load_dotenv(override=True)
    
    # 引数の解析
    args = parse_arguments()
    
    try:
        # 設定の読み込み
        settings = Settings.from_env()
        
        # ログレベルの上書き
        if args.log_level:
            settings.log_level = args.log_level
        
        # 設定の妥当性チェック
        settings.validate()
        
        # ログの設定
        setup_logging(
            log_directory=settings.log_directory,
            log_level=settings.log_level
        )
        
        # コンソール出力のUnicodeエンコーディングを設定
        ensure_utf8_encoding()
        
        # セッションマネージャーの初期化
        session_manager = SessionManager(settings)
        
        # ヘルスチェック
        if args.health_check:
            if await session_manager.health_check():
                print("✅ Azure OpenAI connection OK")
                print("✅ Configuration loaded successfully") 
                print("✅ All systems operational")
                return 0
            else:
                print("❌ System health check failed")
                print("Please check your configuration and API keys")
                return 1
        
        # タスクの決定
        task = args.task
        
        # インタラクティブモードの処理
        if args.interactive:
            print("=== AI Brainstorming System - Interactive Mode ===")
            print("カスタムタスクを入力してください（Enterで既定のタスクを使用）:")
            print()
            user_input = input("タスク: ").strip()
            if user_input:
                task = user_input
            print()
        
        # セッションの実行
        print("Starting AI Brainstorming Session...")
        print("=" * 50)
        
        filename = await session_manager.run_session(task)
        
        print("=" * 50)
        print("Session completed successfully!")
        
        # 統計情報の表示
        stats = session_manager.get_session_stats()
        print(f"Total messages: {stats['total_messages']}")
        print(f"Execution time: {stats['execution_time']:.2f} seconds")
        print(f"Results saved to: {filename}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nSession interrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    asyncio.run(main())