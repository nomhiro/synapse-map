#!/bin/bash

echo "Starting AI Brainstorming Chat Viewer..."
echo

# プロジェクトディレクトリに移動
cd "$(dirname "$0")"

# .venv環境が存在するかチェック
if [ ! -f ".venv/Scripts/python.exe" ]; then
    echo "❌ .venv環境が見つかりません。"
    echo "以下のコマンドで仮想環境を作成してください："
    echo "python -m venv .venv"
    echo "source .venv/Scripts/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# .venv環境のPythonで実行
.venv/Scripts/python.exe scripts/run_streamlit.py