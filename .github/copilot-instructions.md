# GitHub Copilot Instructions

## プロジェクト概要

- **目的**: GitHub Issues を利用したディスク容量監視システム
- **主な機能**:
  - ローカルディスクの使用量を取得（psutil 使用）
  - GitHub API 経由で Issue の読み取り・更新
  - ディスク使用率に基づく視覚的インジケータ（✅ / 🔴）
  - 複数ドライブ対応（Windows/Unix 両対応）
  - 日次ログファイルの自動生成
- **対象ユーザー**: 複数コンピュータのディスク使用状況を集中管理したい開発者・システム管理者

## 共通ルール

- 会話は日本語で行う。
- コミットメッセージは [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) に従う。`<description>` は日本語で記載する。
  - 例: `feat: ユーザー認証機能を追加`
- ブランチ命名は [Conventional Branch](https://conventional-branch.github.io) に従う。`<type>` は短縮形（feat, fix）を使用する。
  - 例: `feat/add-user-auth`
- 日本語と英数字の間には半角スペースを挿入する。

## 技術スタック

- **言語**: Python 3 (3.9, 3.10, 3.11, 3.12, 3.13, 3.x でテスト)
- **主要ライブラリ**:
  - psutil 7.2.1 - ディスク使用量取得
  - requests 2.32.5 - GitHub API 通信
- **テストフレームワーク**: unittest (Python 標準ライブラリ)
- **パッケージマネージャー**: pip
- **CI/CD**: GitHub Actions（Ubuntu/Windows マトリックステスト）

## コーディング規約

- **インデント**: スペース 2 個（`.editorconfig` で定義）
- **改行コード**: LF
- **エンコーディング**: UTF-8
- **命名規則**:
  - クラス: PascalCase（例: `GitHubIssue`）
  - 関数・変数: snake_case（例: `get_disk_usage`）
  - 定数: UPPER_SNAKE_CASE（例: `DEFAULT_LOG_DIR`）
- **コメント**: 日本語で記載
- **エラーメッセージ**: 英語で記載
- **docstring**: 日本語で記載（関数・クラスに必須）

## 開発コマンド

```bash
# 依存関係のインストール
pip install -r requirements.txt

# メインアプリケーション実行
python calculate_storage.py <ISSUE_NUMBER>

# テスト実行
python -m unittest discover -s . -p "test_*.py"

# デプロイ（Linux/Unix）
sudo bash calculate-storage.sh

# デプロイ（Windows PowerShell）
.\calculate-storage.ps1
```

## テスト方針

- **テストフレームワーク**: unittest
- **テストファイル**: `test_calculate_storage.py`
- **モック**: `unittest.mock` を使用してネットワーク通信や外部依存をモック化
- **テスト追加の方針**:
  - 新機能追加時は対応するユニットテストを必ず追加
  - GitHub API 通信部分は必ずモック化
  - Windows/Unix 両対応が必要な機能は OS 別にテスト
  - エラーハンドリングのテストも含める

## セキュリティ / 機密情報

- GitHub Personal Access Token などの認証情報はコードに直接記述しない（ハードコード禁止）。
- 現行実装では GitHub Personal Access Token は `data/github_token.txt` から読み込む想定とし、`data/` ディレクトリは Git 管理から除外する。
- 認証情報は Git にコミットしない。
- ログに認証情報や個人情報を出力しない。
- `.gitignore` で `data/` と `results/` ディレクトリを除外している（機密情報や一時ファイル用）。将来的に環境変数での管理に切り替える場合は、コード実装とこのドキュメントの両方を更新すること。

## ドキュメント更新

以下のファイルは機能追加・変更時に更新すること：

- **requirements.txt**: 依存パッケージ追加・更新時
- **test_calculate_storage.py**: テストケース追加時
- **このファイル（.github/copilot-instructions.md）**: 開発手順やルールの変更時

## リポジトリ固有

- **環境変数**:
  - `GITHUB_REPOSITORY`: GitHub リポジトリ名（CI 実行時に自動設定）
  - `CALCULATE_STORAGE_LOG_DIR`: ログ出力ディレクトリ（未指定時は OS ごとのデフォルトパス）
  - `ISSUE_NUMBER`: GitHub Issue 番号。デプロイスクリプトで環境変数として設定し、アプリ本体にはコマンドライン引数（`sys.argv[1]`）として渡される。
- **GitHub Issue フォーマット**:
  - `<!-- calculate-storage#<computer_name>#<drive> -->` コメントが付いた行のみを自動更新対象とする
  - 行の Markdown 部分は `|` で split して解析・更新し、容量は MB 単位で表示する
- **ログファイル**: 日次ログを `YYYY-MM-DD.log` 形式で出力
- **デプロイスクリプト**: Linux は bash、Windows は PowerShell で自動デプロイ可能
- **Renovate**: 依存パッケージ更新は自動 PR で管理
