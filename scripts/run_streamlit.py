"""
Streamlit Chat Viewer 起動スクリプト
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Streamlitアプリケーションを起動する"""
    
    # プロジェクトルートを取得
    project_root = Path(__file__).parent.parent
    streamlit_app_path = project_root / "src" / "web" / "streamlit_app.py"
    
    # 作業ディレクトリをプロジェクトルートに変更
    os.chdir(project_root)
    
    # .venv環境のPythonパスを取得
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    
    # .venv環境が存在するかチェック
    if not venv_python.exists():
        print("❌ .venv環境が見つかりません。")
        print("以下のコマンドで仮想環境を作成してください：")
        print("python -m venv .venv")
        print(".venv\\Scripts\\activate")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # Streamlitアプリケーションを起動
    cmd = [
        str(venv_python), "-m", "streamlit", "run", 
        str(streamlit_app_path),
        "--server.port", "8501",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false"
    ]
    
    print("🚀 Streamlit Chat Viewerを起動しています...")
    print(f"📂 作業ディレクトリ: {project_root}")
    print(f"🐍 Python環境: {venv_python}")
    print(f"📄 アプリケーション: {streamlit_app_path}")
    print(f"🌐 URL: http://localhost:8501")
    print("-" * 50)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Streamlitの起動に失敗しました: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Streamlitアプリケーションを停止しました。")
        sys.exit(0)

if __name__ == "__main__":
    main()