"""
Production Run Script - 本番環境での実行スクリプト
"""

import sys
import os
import asyncio

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main import main

if __name__ == "__main__":
    # 本番環境用の設定
    os.environ.setdefault('ENVIRONMENT', 'production')
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nProduction session interrupted")
        sys.exit(1)