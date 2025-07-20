@echo off
echo Starting AI Brainstorming Chat Viewer...
echo.

cd /d "%~dp0"

REM .venv環境が存在するかチェック
if not exist ".venv\Scripts\python.exe" (
    echo ❌ .venv環境が見つかりません。
    echo 以下のコマンドで仮想環境を作成してください：
    echo python -m venv .venv
    echo .venv\Scripts\activate
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

REM .venv環境のPythonで実行
.venv\Scripts\python.exe scripts/run_streamlit.py

pause