# Gemini CLI 作業方針

## 目的

このドキュメントは、Gemini CLI が calculate-storage プロジェクトで作業を行う際のコンテキストと作業方針を定義します。

## 出力スタイル

- **言語**: 日本語で応答する
- **トーン**: 簡潔かつ明確に、技術的な正確さを重視
- **形式**: Markdown 形式で構造化された出力を提供

## 共通ルール

- 会話は日本語で行う。
- コミットメッセージは [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) に従う。`<description>` は日本語で記載する。
  - 例: `feat: ユーザー認証機能を追加`
- ブランチ命名は [Conventional Branch](https://conventional-branch.github.io) に従う。`<type>` は短縮形（feat, fix）を使用する。
  - 例: `feat/add-user-auth`
- 日本語と英数字の間には半角スペースを挿入する。

## プロジェクト概要

**calculate-storage** は、GitHub Issues を利用したディスク容量監視システムです。

- **目的**: 複数のコンピュータのディスク使用状況を GitHub Issue で集中管理
- **主な機能**:
  - psutil によるローカルディスク使用量の取得
  - GitHub API（requests）による Issue の読み取り・更新
  - ディスク使用率に基づく視覚的インジケータ（✅ OK / 🔴 危険）
  - 複数ドライブ対応（Windows/Unix 両対応）
  - 日次ログファイルの自動生成（YYYY-MM-DD.log 形式）
  - JSON 形式での結果保存
- **対象ユーザー**: 複数コンピュータのディスク使用状況を集中管理したい開発者・システム管理者

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

## Gemini CLI の役割

Gemini CLI は、以下の場合に相談を受けることがあります：

- **GitHub API 仕様**: レート制限、認証方法、エンドポイント仕様などの最新情報
- **Python バージョン差**: Python 3.9-3.13 間の仕様差や非互換性
- **psutil ライブラリ**: ディスク情報取得の最新仕様や OS 別の挙動
- **requests ライブラリ**: HTTP 通信の最新仕様やセキュリティベストプラクティス
- **外部依存の前提条件**: GitHub API のクォータ、OS 別のディスク情報取得方法など

## 注意事項

- **認証情報のコミット禁止**: GitHub Personal Access Token などの認証情報を Git にコミットしない
- **ログへの機密情報出力禁止**: 認証情報や個人情報をログに出力しない
- **既存ルールの優先**: プロジェクトの `.editorconfig` や既存のコーディングスタイルを尊重する
- **既知の制約**:
  - GitHub API のレート制限（認証なし: 60 req/h、認証あり: 5000 req/h）
  - psutil のディスク情報は OS により取得方法が異なる（Windows: ドライブレター、Unix: マウントポイント）
  - unittest.mock を使用してネットワーク通信や外部依存をモック化すること

## リポジトリ固有

### 環境変数

- **`GITHUB_REPOSITORY`**: GitHub リポジトリ名（CI 実行時に自動設定）
- **`CALCULATE_STORAGE_LOG_DIR`**: ログ出力ディレクトリ（未指定時は OS ごとのデフォルトパス）
- **`ISSUE_NUMBER`**: GitHub Issue 番号（実行時引数で指定）

### GitHub Issue フォーマット

GitHub Issue 本文は Markdown テーブル形式：

```markdown
| Host | Drive | Used | Total | Usage | Status |
|------|-------|------|-------|-------|--------|
| hostname1 | C: | 100000 MB | 500000 MB | 20% | ✅ OK |
| hostname2 | D: | 450000 MB | 500000 MB | 90% | 🔴 危険 |
```

- 正規表現パターン: `\| (.+) \| (.+) \| (.+) MB \| (.+) MB \| (.+)% \| (.+) \|`
- ホスト名が一致する行を更新、一致しない行はそのまま保持
- 新しいホストの場合は行を追加

### 主要クラス

- **`GitHubIssue`**: GitHub Issue の読み取り・解析・更新を担当
  - `get_issue_body()`: Issue 本文を取得
  - `parse_issue_body()`: Markdown テーブルを解析
  - `update_issue_body()`: Issue 本文を更新

### CI/CD

- **GitHub Actions**: `.github/workflows/ci.yml`
- **マトリックステスト**: Ubuntu/Windows × Python 3.9-3.13
- **テストコマンド**: `python -m unittest discover -s . -p "test_*.py"`
