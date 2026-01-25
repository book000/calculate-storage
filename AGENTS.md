# AI エージェント作業方針

## 目的

このドキュメントは、汎用 AI エージェントが calculate-storage プロジェクトで作業を行う際の共通方針を定義します。

## 基本方針

- **会話言語**: 日本語
- **コード内コメント**: 日本語
- **エラーメッセージ**: 英語
- **日本語と英数字の間**: 半角スペースを挿入
- **コミットメッセージ**: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) に従う。`<description>` は日本語で記載
  - 例: `feat: ディスク使用率アラート機能を追加`

## 判断記録のルール

AI エージェントは判断を必ずレビュー可能な形で記録すること：

1. **判断内容の要約**: 何を決定したかを明記
2. **検討した代替案**: 他に考慮した選択肢を列挙
3. **採用しなかった案とその理由**: なぜその案を選ばなかったかを説明
4. **前提条件・仮定・不確実性**: 判断の前提となる情報や不確実な要素を明示

**重要**: 前提・仮定・不確実性を明示すること。仮定を事実のように扱ってはならない。

## プロジェクト概要

**calculate-storage** は、GitHub Issues を利用したディスク容量監視システムです。

- **目的**: 複数のコンピュータのディスク使用状況を GitHub Issue で集中管理
- **主な機能**:
  - psutil によるローカルディスク使用量の取得
  - GitHub API（requests）による Issue の読み取り・更新
  - ディスク使用率に基づく視覚的インジケータ（✅ OK / 🔴 危険）
  - 複数ドライブ対応（Windows/Unix 両対応）
  - 日次ログファイルの自動生成
- **技術スタック**: Python 3、psutil、requests、unittest

## 開発手順（概要）

1. **プロジェクト理解**:
   - `calculate_storage.py` と `test_calculate_storage.py` を読み、アーキテクチャを理解する
   - GitHub Issue のフォーマット（Markdown テーブル）を確認する

2. **依存関係インストール**:
   ```bash
   pip install -r requirements.txt
   ```

3. **変更実装**:
   - 関数やクラスには docstring を日本語で記載する
   - エラーメッセージは英語で記載する
   - 日本語と英数字の間には半角スペースを挿入する

4. **テストと Lint/Format 実行**:
   ```bash
   # テスト実行
   python -m unittest discover -s . -p "test_*.py"
   ```

5. **コミット**:
   - Conventional Commits に従ったコミットメッセージを作成
   - 例: `feat: ディスク使用率アラート機能を追加`

## テスト方針

- **テストフレームワーク**: unittest (Python 標準ライブラリ)
- **テストファイル**: `test_calculate_storage.py`
- **モック**: `unittest.mock` を使用してネットワーク通信や外部依存をモック化
- **テスト追加の方針**:
  - 新機能追加時は対応するユニットテストを必ず追加
  - GitHub API 通信部分は必ずモック化
  - Windows/Unix 両対応が必要な機能は OS 別にテスト
  - エラーハンドリングのテストも含める

## セキュリティ / 機密情報

- GitHub Personal Access Token などの認証情報は環境変数で管理し、コードに直接記述しない。
- 認証情報は Git にコミットしない。
- ログに認証情報や個人情報を出力しない。
- `.gitignore` で `data/` と `results/` ディレクトリを除外している（機密情報や一時ファイル用）。

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

### 主要クラスと関数

- **`GitHubIssue`**: GitHub Issue の読み取り・解析・更新を担当
  - `get_issue_body()`: Issue 本文を取得
  - `parse_issue_body()`: Markdown テーブルを解析
  - `update_issue_body()`: Issue 本文を更新

### CI/CD

- **GitHub Actions**: `.github/workflows/ci.yml`
- **マトリックステスト**: Ubuntu/Windows × Python 3.9-3.13
- **テストコマンド**: `python -m unittest discover -s . -p "test_*.py"`
