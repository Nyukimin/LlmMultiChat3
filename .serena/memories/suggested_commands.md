# 推奨コマンド: LlmMultiChat3

## 📋 プロジェクト管理（Windows環境）

### Git操作
```cmd
# 現在の状態確認
git status

# 変更をステージング
git add .

# コミット
git commit -m "コミットメッセージ"

# プッシュ
git push

# プル
git pull

# ブランチ一覧
git branch

# 新規ブランチ作成・切替
git checkout -b feature/新機能名

# ブランチ切替
git checkout main
```

### ファイル操作（Windows CMD/PowerShell）
```cmd
# ディレクトリ一覧（CMD）
dir

# ディレクトリ一覧（PowerShell）
ls

# ディレクトリ移動
cd docks
cd ..

# ファイル検索（CMD）
dir /s /b *.py

# ファイル検索（PowerShell）
Get-ChildItem -Recurse -Filter *.py

# ファイル内容表示
type README.md

# テキスト検索（PowerShell）
Select-String -Path "docks/*.md" -Pattern "API"
```

## 🐍 Python開発（将来の実装時）

### 環境構築
```cmd
# 仮想環境作成
python -m venv venv

# 仮想環境有効化（CMD）
venv\Scripts\activate.bat

# 仮想環境有効化（PowerShell）
venv\Scripts\Activate.ps1

# 依存関係インストール
pip install -r requirements.txt

# 依存関係更新
pip freeze > requirements.txt
```

### コード品質
```cmd
# リンティング（flake8）
flake8 .

# フォーマット（black）
black .

# 型チェック（mypy）
mypy .

# インポート整理（isort）
isort .
```

### テスト
```cmd
# pytest実行
pytest

# カバレッジ付きテスト
pytest --cov=.

# 詳細出力
pytest -v

# 特定ファイルのみ
pytest tests/test_memory.py
```

## 🚀 アプリケーション実行（将来の実装時）

### メインアプリ
```cmd
# メイン起動
python main.py

# システムチェック
python check_system.py

# 開発モード（デバッグログ有効）
python main.py --debug
```

### Ollama操作
```cmd
# Ollama起動
ollama serve

# モデル一覧
ollama list

# モデル取得
ollama pull llama3-jp
ollama pull mistral

# モデル削除
ollama rm モデル名
```

### データベース（将来の実装時）
```cmd
# Redis起動（WSL/Docker必要）
redis-server

# Redis CLI
redis-cli

# Neo4j起動（Docker推奨）
docker run --name neo4j -p 7474:7474 -p 7687:7687 neo4j

# PostgreSQL起動（Docker推奨）
docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres
```

## 📚 ドキュメント操作

### Markdown編集
```cmd
# VSCodeでドキュメント開く
code docks\会話LLM_仕様.md

# 複数ファイル開く
code README.md docks\会話LLM_仕様.md docks\会話LLM_実装仕様書.md
```

### ドキュメント検索
```powershell
# PowerShellでキーワード検索
Select-String -Path "docks\*.md" -Pattern "API|MCP|自律" -CaseSensitive

# ファイル行数カウント
(Get-Content docks\会話LLM_仕様.md).Count
```

## 🔧 開発ツール

### VSCode拡張機能（推奨）
- Python
- Pylance
- Jupyter
- GitLens
- Markdown All in One
- Even Better TOML

### プロジェクト固有コマンド（将来追加予定）
```cmd
# ETL実行（知識ベース更新）
python kb/etl_movie.py
python kb/etl_history.py

# 記憶DBバックアップ
python scripts/backup_memories.py

# キャラクター追加
python scripts/add_character.py --name "カスタム1" --config personas/custom1.yaml
```

## 🐳 Docker操作（将来の実装時）
```cmd
# Docker Compose起動
docker-compose up -d

# ログ確認
docker-compose logs -f

# 停止
docker-compose down

# 再ビルド
docker-compose up --build
```

## ⚠️ 現在の開発フェーズ
**Phase 1（仕様策定中）**: 実装前のため、Python/Ollama/DB関連コマンドはまだ使用不可。
**現在利用可能**: Git、ファイル操作、ドキュメント編集のみ。
