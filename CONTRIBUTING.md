# 🤝 Contributing to AI Brainstorming System

AI Brainstorming System プロジェクトへのコントリビューションを歓迎します！このドキュメントでは、プロジェクトへの貢献方法について説明します。

## 📋 コントリビューションの種類

### 🐛 バグ報告
- システムの動作不良
- エラーメッセージの改善
- ドキュメントの誤り

### ✨ 機能提案
- 新しいエージェントタイプ
- UI/UX の改善
- パフォーマンス向上

### 📚 ドキュメント改善
- セットアップガイドの改善
- コードコメントの追加
- 使用例の追加

### 🛠️ コード改善
- バグ修正
- 新機能実装
- コード品質の向上

## 🚀 始め方

### 1. 開発環境のセットアップ

```bash
# リポジトリをフォーク後、クローン
git clone https://github.com/your-username/ai-brainstorming-system.git
cd ai-brainstorming-system

# 仮想環境作成
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 開発用依存関係インストール
pip install -r requirements-dev.txt
```

### 2. 開発用設定

```bash
# pre-commit フックを設定
pre-commit install

# 環境変数設定
cp .env.example .env
# .env ファイルを編集
```

### 3. ブランチ作成

```bash
# 最新のmainブランチを取得
git checkout main
git pull upstream main

# 機能ブランチを作成
git checkout -b feature/your-feature-name
```

## 🔧 開発ガイドライン

### コードスタイル

#### Python コーディング規約
- **PEP 8** に従う
- **Type hints** を使用する
- **Docstrings** を記述する（Google スタイル）

```python
def create_agent(name: str, system_message: str) -> AssistantAgent:
    """エージェントを作成する
    
    Args:
        name: エージェント名
        system_message: システムメッセージ
        
    Returns:
        作成されたエージェント
        
    Raises:
        ValueError: 無効な名前の場合
    """
    pass
```

#### ファイル構成
- **モジュラー設計**: 機能ごとにファイルを分離
- **設定分離**: ハードコーディングを避ける
- **エラーハンドリング**: 適切な例外処理

### コード品質チェック

#### 実行前チェック
```bash
# コードフォーマット
black src/
isort src/

# 型チェック
mypy src/

# リンター
flake8 src/

# セキュリティチェック
bandit -r src/
```

#### テスト実行
```bash
# 全てのテスト実行
pytest

# カバレッジ付きテスト
pytest --cov=src --cov-report=html

# 特定のテストファイル
pytest tests/test_agent_manager.py
```

## 📝 プルリクエストのガイドライン

### 1. プルリクエスト前のチェックリスト

- [ ] コードが動作することを確認
- [ ] テストが通ることを確認
- [ ] ドキュメントを更新（必要に応じて）
- [ ] CHANGELOG.md を更新（該当する場合）
- [ ] コミットメッセージが明確

### 2. プルリクエストのテンプレート

```markdown
## 概要
このプルリクエストの目的と変更内容を簡潔に説明

## 変更内容
- [ ] 新機能追加
- [ ] バグ修正
- [ ] ドキュメント更新
- [ ] リファクタリング

## 詳細な変更点
1. 変更点1の詳細
2. 変更点2の詳細

## テスト
- [ ] 既存テストが通る
- [ ] 新しいテストを追加（該当する場合）
- [ ] 手動テストを実施

## スクリーンショット（UI変更の場合）
変更前後の画面キャプチャ

## 関連Issue
Closes #123
```

### 3. コミットメッセージ規約

[Conventional Commits](https://www.conventionalcommits.org/) 形式を使用：

```bash
# 新機能
feat: add new market analysis agent

# バグ修正
fix: resolve CosmosDB connection timeout issue

# ドキュメント
docs: update setup guide for macOS

# リファクタリング
refactor: extract common agent logic

# テスト
test: add unit tests for session manager

# 設定
chore: update dependencies
```

## 🧪 テストガイドライン

### テスト構成
```
tests/
├── unit/           # 単体テスト
├── integration/    # 統合テスト
├── fixtures/       # テストデータ
└── conftest.py     # 共通設定
```

### テスト作成指針

#### 1. 単体テスト
```python
import pytest
from src.core.agent_manager import AgentManager

class TestAgentManager:
    """エージェントマネージャーのテスト"""
    
    def test_create_agent_success(self):
        """エージェント作成の成功ケース"""
        manager = AgentManager()
        agent = manager.create_agent("test_agent", "test message")
        assert agent.name == "test_agent"
    
    def test_create_agent_invalid_name(self):
        """無効な名前でのエージェント作成"""
        manager = AgentManager()
        with pytest.raises(ValueError):
            manager.create_agent("", "test message")
```

#### 2. 統合テスト
```python
@pytest.mark.integration
def test_full_session_workflow():
    """完全なセッションワークフローのテスト"""
    # セッション作成からエージェント実行まで
    pass
```

### モックの使用
```python
from unittest.mock import Mock, patch

@patch('src.core.cosmosdb_manager.CosmosClient')
def test_cosmosdb_save(mock_client):
    """CosmosDB保存のテスト"""
    mock_client.return_value.create_item.return_value = {"id": "test"}
    # テスト実装
```

## 📖 ドキュメント作成

### ドキュメント種類
- **README.md**: プロジェクト概要
- **SETUP.md**: セットアップガイド
- **API Documentation**: コード内docstring
- **User Guide**: 使用方法説明

### ドキュメント作成時の注意点
1. **明確で簡潔な説明**
2. **実際のコード例を含める**
3. **スクリーンショットの追加（UI関連）**
4. **多言語対応**（日本語・英語）

## 🏷️ Issue とラベル

### Issue テンプレート

#### バグ報告
```markdown
## バグの概要
何が起こったかの簡潔な説明

## 再現手順
1. ○○を実行
2. ○○をクリック
3. エラーが発生

## 期待される動作
何が起こるべきだったかの説明

## 実際の動作
実際に何が起こったかの説明

## 環境
- OS: [例: Windows 10]
- Python: [例: 3.11.0]
- バージョン: [例: v1.0.0]

## 追加情報
ログ、スクリーンショットなど
```

#### 機能要望
```markdown
## 機能の概要
提案する機能の簡潔な説明

## 動機・背景
なぜこの機能が必要かの説明

## 詳細な説明
機能の詳細仕様

## 代替案
検討した他の解決方法

## 参考情報
関連リンク、参考実装など
```

### ラベル体系
- **type**: `bug`, `enhancement`, `documentation`
- **priority**: `low`, `medium`, `high`, `critical`
- **difficulty**: `beginner`, `intermediate`, `advanced`
- **area**: `agents`, `ui`, `database`, `api`

## 🚢 リリースプロセス

### バージョニング
[Semantic Versioning](https://semver.org/) を使用：
- **MAJOR**: 破壊的変更
- **MINOR**: 後方互換な機能追加
- **PATCH**: 後方互換なバグ修正

### リリース手順
1. **CHANGELOG.md** 更新
2. **バージョンタグ** 作成
3. **GitHub Release** 作成
4. **PyPI パッケージ** 公開（将来）

## 🎯 優先的な貢献エリア

### 🔥 高優先度
- バグ修正とパフォーマンス改善
- ドキュメントの改善
- テストカバレッジの向上

### 💡 新機能
- 新しいエージェントタイプ
- 分析・レポート機能
- 多言語対応

### 🎨 UI/UX
- Streamlit ダッシュボードの改善
- モバイル対応
- アクセシビリティ向上

## 📞 コミュニケーション

### 質問・相談
- **GitHub Discussions**: 一般的な質問
- **GitHub Issues**: バグ報告・機能要望
- **Email**: project-email@example.com

### コードレビュー
- **建設的なフィードバック** を心がける
- **説明的なコメント** を書く
- **代替案の提示** をする

## 🏆 コントリビューター認定

### 貢献レベル
- **コントリビューター**: 1つ以上のPR
- **レギュラーコントリビューター**: 5つ以上のPR
- **メンテナー**: 継続的な貢献と責任

### 認定特典
- **README.md** への名前掲載
- **優先レビュー** 権限
- **プロジェクト方針** への参加

---

## 🙏 謝辞

すべてのコントリビューターの皆様に感謝いたします。あなたの貢献がこのプロジェクトをより良いものにします！

[![Contributors](https://contrib.rocks/image?repo=your-username/ai-brainstorming-system)](https://github.com/your-username/ai-brainstorming-system/graphs/contributors)