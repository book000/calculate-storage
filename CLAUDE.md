# Claude Code 作業方針

## 目的

このドキュメントは、Claude Code が calculate-storage プロジェクトで作業を行う際の方針とプロジェクト固有ルールを定義します。

## 判断記録のルール

Claude Code は判断を必ずレビュー可能な形で記録すること：

1. **判断内容の要約**: 何を決定したかを明記
2. **検討した代替案**: 他に考慮した選択肢を列挙
3. **採用しなかった案とその理由**: なぜその案を選ばなかったかを説明
4. **前提条件・仮定・不確実性**: 判断の前提となる情報や不確実な要素を明示
5. **他エージェントによるレビュー可否**: Codex CLI や Gemini CLI によるレビューが必要かを示す

**重要**: 前提・仮定・不確実性を明示すること。仮定を事実のように扱ってはならない。

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

## 重要ルール

- **会話言語**: 日本語
- **コード内コメント**: 日本語
- **エラーメッセージ**: 英語
- **日本語と英数字の間**: 半角スペースを挿入
- **コミットメッセージ**: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) に従う。`<description>` は日本語で記載
  - 例: `feat: ディスク使用率アラート機能を追加`
- **ブランチ命名**: [Conventional Branch](https://conventional-branch.github.io) に従う。`<type>` は短縮形（feat, fix）を使用
  - 例: `feat/add-alert-feature`

## 環境のルール

- **GitHub リポジトリ調査**: 調査のために GitHub リポジトリを参照する場合は、テンポラリディレクトリに `git clone` して、そこでコード検索する
- **Renovate PR**: Renovate が作成した既存のプルリクエストに対して、追加コミットや更新を行ってはならない

## コード改修時のルール

- **日本語と英数字の間**: 半角スペースを挿入しなければならない
- **エラーメッセージの絵文字**: 既存のエラーメッセージで先頭に絵文字がある場合は、全体で統一する。エラーメッセージに即した一文字の絵文字を使用
- **docstring**: 関数やクラスには docstring を日本語で記載・更新する

## 相談ルール

Claude Code は他エージェントに相談することができます。以下の観点で使い分けてください：

### Codex CLI (ask-codex)

以下の場合に Codex CLI を使用：

- 実装コードに対するソースコードレビュー
- 関数設計、モジュール内部の実装方針などの局所的な技術判断
- アーキテクチャ、モジュール間契約、パフォーマンス／セキュリティといった全体影響の判断
- 実装の正当性確認、機械的ミスの検出、既存コードとの整合性確認

### Gemini CLI (ask-gemini)

以下の場合に Gemini CLI を使用：

- GitHub API 仕様、Python バージョン差、レート制限・クォータといった、最新の適切な情報が必要な外部依存の判断
- 外部一次情報の確認、最新仕様の調査、外部前提条件の検証

### 指摘への対応ルール

他エージェントが指摘・異議を提示した場合、Claude Code は必ず以下のいずれかを行う。**黙殺・無言での不採用は禁止する**。

- 指摘を受け入れ、判断を修正する
- 指摘を退け、その理由を明示する

以下は必ず実施すること：

- 他エージェントの提案を鵜呑みにせず、その根拠や理由を理解する
- 自身の分析結果と他エージェントの意見が異なる場合は、双方の視点を比較検討する
- 最終的な判断は、両者の意見を総合的に評価した上で、自身で下す

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

## アーキテクチャと主要ファイル

### アーキテクチャサマリー

```
GitHub Issue (Markdown テーブル)
         ↕ GitHub API (requests)
  GitHubIssue クラス
         ↓ 解析・更新
  ディスク情報取得 (psutil)
         ↓
  JSON 出力 + ログ記録
```

### 主要ファイル

| ファイル | 説明 |
|---------|------|
| `calculate_storage.py` | メインアプリケーション（約 326 行） |
| `test_calculate_storage.py` | ユニットテスト（約 302 行） |
| `requirements.txt` | 依存パッケージ一覧（psutil, requests） |
| `calculate-storage.sh` | Linux/Unix デプロイスクリプト |
| `calculate-storage.ps1` | Windows デプロイスクリプト |
| `.editorconfig` | エディタ設定（UTF-8, LF, スペース 2 個インデント） |
| `.github/workflows/ci.yml` | GitHub Actions CI/CD 設定 |

### 主要クラス

- **`GitHubIssue`**: GitHub Issue の読み取り・解析・更新を担当
  - `get_issue_body()`: Issue 本文を取得
  - `parse_issue_body()`: Markdown テーブルを解析
  - `update_issue_body()`: Issue 本文を更新

## 実装パターン

### 推奨パターン

- **正規表現によるテーブル解析**: `re.compile(r'\| (.+) \| (.+) \| (.+) MB \| (.+) MB \| (.+)% \| (.+) \|')` でホスト行を解析
- **unittest.mock による外部依存のモック化**: GitHub API 通信や psutil の戻り値をモック化してテスト
- **OS 判定**: `platform.system()` で Windows/Unix を判別し、適切なパス・ホスト名取得方法を選択
- **ログ記録**: `logging` モジュールを使用し、日次ログファイルに記録
- **エラーハンドリング**: GitHub API エラー、ディスクアクセスエラー、JSON 解析エラーを適切に処理

### 非推奨パターン

- **ハードコードされた認証情報**: 環境変数や GitHub Actions のシークレットを使用すること
- **モックなしの外部通信テスト**: テストは必ず `unittest.mock` でモック化すること
- **プラットフォーム依存コードの無条件実行**: OS 判定を行い、適切に分岐させること

## テスト

### テスト方針

- **テストフレームワーク**: unittest (Python 標準ライブラリ)
- **テストファイル**: `test_calculate_storage.py`
- **モック**: `unittest.mock.patch` を使用
- **テスト実行**: `python -m unittest discover -s . -p "test_*.py"`

### 追加テスト条件

以下の場合は必ずテストを追加：

1. 新機能追加時
2. GitHub API 通信ロジックの変更時
3. ディスク情報取得ロジックの変更時
4. エラーハンドリングの変更時
5. Windows/Unix 両対応が必要な機能の追加時

## ドキュメント更新ルール

### 更新対象

以下のファイルは機能追加・変更時に更新すること：

- **requirements.txt**: 依存パッケージ追加・更新時
- **test_calculate_storage.py**: テストケース追加時
- **.github/copilot-instructions.md**: 開発手順やルールの変更時
- **このファイル（CLAUDE.md）**: アーキテクチャや実装パターンの変更時

### 更新タイミング

- **機能追加時**: 実装完了後、テスト追加と同時に更新
- **API 変更時**: 変更内容を反映
- **環境変数追加時**: ドキュメントに追記

## 作業チェックリスト

### 新規改修時

新規改修を行う前に、以下を必ず確認すること：

1. プロジェクトについて詳細に探索し理解すること
2. 作業を行うブランチが適切であること。すでに PR を提出しクローズされたブランチでないこと
3. 最新のリモートブランチに基づいた新規ブランチであること
4. PR がクローズされ、不要となったブランチは削除されていること
5. `pip install -r requirements.txt` で依存パッケージをインストールしたこと

### コミット・プッシュ前

コミット・プッシュする前に、以下を必ず確認すること：

1. コミットメッセージが Conventional Commits に従っていること（`<description>` は日本語）
2. コミット内容にセンシティブな情報（GitHub Token など）が含まれていないこと
3. テストが成功すること: `python -m unittest discover -s . -p "test_*.py"`
4. 動作確認を行い、期待通り動作すること

### プルリクエスト作成前

プルリクエストを作成する前に、以下を必ず確認すること：

1. プルリクエストの作成をユーザーから依頼されていること
2. コミット内容にセンシティブな情報が含まれていないこと
3. コンフリクトする恐れが無いこと

### プルリクエスト作成後

プルリクエストを作成した後は、以下を必ず実施すること。**PR 作成後のプッシュ時に毎回実施してください**。

時間がかかる処理が多いため、Task を使って並列実行すること：

1. コンフリクトが発生していないことを確認する
2. PR 本文の内容は、ブランチの現在の状態を、今までのこの PR での更新履歴を含むことなく、最新の状態のみ、漏れなく日本語で記載されていること。この PR を見たユーザーが、最終的にどのような変更を含む PR なのかをわかりやすく、細かく記載されていること
3. `gh pr checks <PR ID> --watch` で GitHub Actions CI を待ち、その結果がエラーとなっていないこと。成功している場合でも、ログを確認し、誤って成功扱いになっていないこと。もし GitHub Actions が動作しない場合は、ローカルで CI と同等のテストを行い、CI が成功することを保証しなければならない
4. `request-review-copilot` コマンドが存在する場合、`request-review-copilot https://github.com/$OWNER/$REPO/pull/$PR_NUMBER` で GitHub Copilot へレビューを依頼すること。レビュー依頼は自動で行われる場合もあるし、制約により `request-review-copilot` を実行しても GitHub Copilot がレビューしないケースがある
5. 10 分以内に投稿される GitHub Copilot レビューへの対応を行うこと。対応したら、レビューコメントそれぞれに対して返信を行うこと。レビュアーに GitHub Copilot がアサインされていない場合はスキップして構わない
6. `/code-review:code-review` によるコードレビューを実施したこと。コードレビュー内容に対しては、**スコアが 50 以上の指摘事項** に対して対応してください（80 がボーダーラインではありません）

## リポジトリ固有

### 環境変数

- **`GITHUB_REPOSITORY`**: GitHub リポジトリ名（CI 実行時に自動設定）
- **`CALCULATE_STORAGE_LOG_DIR`**: ログ出力ディレクトリ（未指定時は OS ごとのデフォルトパス）
- **`ISSUE_NUMBER`**: GitHub Issue 番号（実行時引数で指定）

### GitHub Issue フォーマット

GitHub Issue 本文は以下のような Markdown テーブル形式：

```markdown
| Host | Drive | Used | Total | Usage | Status |
|------|-------|------|-------|-------|--------|
| hostname1 | C: | 100000 MB | 500000 MB | 20% | ✅ OK |
| hostname2 | D: | 450000 MB | 500000 MB | 90% | 🔴 危険 |
```

- 正規表現パターン: `\| (.+) \| (.+) \| (.+) MB \| (.+) MB \| (.+)% \| (.+) \|`
- ホスト名が一致する行を更新、一致しない行はそのまま保持
- 新しいホストの場合は行を追加

### ログファイル

- 日次ログファイル: `YYYY-MM-DD.log` 形式
- ログレベル: DEBUG/INFO
- ログディレクトリ: `CALCULATE_STORAGE_LOG_DIR` 環境変数で指定（未指定時は OS デフォルト）

### デプロイ

- **Linux/Unix**: `calculate-storage.sh` スクリプトで自動デプロイ
- **Windows**: `calculate-storage.ps1` スクリプトで自動デプロイ

### CI/CD

- **GitHub Actions**: `.github/workflows/ci.yml`
- **マトリックステスト**: Ubuntu/Windows × Python 3.9-3.13
- **テストコマンド**: `python -m unittest discover -s . -p "test_*.py"`
