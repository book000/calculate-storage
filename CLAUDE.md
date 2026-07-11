# CLAUDE.md

Claude Code が calculate-storage で作業する際のプロジェクト固有ルールを定義します。

## プロジェクト概要

**calculate-storage** は、GitHub Issue をダッシュボードとして複数マシンのディスク使用量を集中管理するツールです。各マシン上で `calculate_storage.py` を実行すると、自ホストのディスク使用量を psutil で取得し、対象 Issue 本文の Markdown テーブルのうち自ホストに対応する行を GitHub API 経由で更新します。使用率が 90% を超えた行には 🔴、それ以外には ✅ を付けます。

## 開発コマンド

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 実行（引数に対象 Issue 番号を渡す）
python calculate_storage.py <ISSUE_NUMBER>

# テスト実行
python -m unittest discover -s . -p "test_*.py"

# デプロイ（Linux/Unix、要 root）
sudo bash calculate-storage.sh

# デプロイ（Windows PowerShell）
.\calculate-storage.ps1
```

CI（`.github/workflows/ci.yml`）は Ubuntu/Windows × Python 3.10〜3.13/3.x のマトリックスで上記テストコマンドを実行します（`requests` が 2.33.0 以降で Python 3.9 サポートを終了したため、Python 3.9 は対象外）。

## コーディング規約

- **会話・コメント・docstring**: 日本語。関数・クラスには日本語 docstring を付ける。
- **エラーメッセージ / ログメッセージ**: 英語。
- **日本語と英数字の間**: 半角スペースを挿入する。
- **インデント**: スペース 2 個（`.editorconfig`。Python も 2 スペース）。改行 LF、UTF-8、末尾改行あり。
- **命名**: クラスは PascalCase、関数・変数は snake_case、定数は UPPER_SNAKE_CASE。
- **コミットメッセージ**: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)。`<description>` は日本語（例: `feat: ディスク使用率アラート機能を追加`）。
- **ブランチ命名**: [Conventional Branch](https://conventional-branch.github.io) 短縮形（例: `feat/add-alert-feature`）。

## アーキテクチャと主要ファイル

| ファイル | 説明 |
|---------|------|
| `calculate_storage.py` | メインアプリケーション（単一ファイル、約 326 行） |
| `test_calculate_storage.py` | unittest ベースのユニットテスト |
| `requirements.txt` | 依存パッケージ（`psutil==7.2.2`, `requests==2.34.2`） |
| `calculate-storage.sh` / `.ps1` | Linux/Windows デプロイスクリプト |
| `.github/workflows/ci.yml` | CI 設定 |
| `.github/copilot-instructions.md` | GitHub Copilot コードレビュー用の指示 |

### 主要な構成要素（`calculate_storage.py`）

- **`setup_logging()`**: 日次ログファイル `YYYY-MM-DD.log` を作成。ファイルハンドラは DEBUG、ストリームハンドラは INFO。出力先は環境変数 `CALCULATE_STORAGE_LOG_DIR`、未指定時は OS ごとのデフォルト（Unix: `/opt/calculate-storage/logs`、Windows: `%USERPROFILE%\calculate-storage\logs`）。
- **`GitHubIssue` クラス**: Issue 本文の取得・解析・更新を担当。
  - `__init__`: 生成時に `__get_issue_body()`（本文取得）と `__get_storage_rows()`（本文解析）を呼ぶ。
  - `update_storage_row(computer_name, drive, usage)`: 対象行のチェックマーク・使用量・容量を更新。使用率 > 90% で 🔴、それ以外で ✅。
  - `get_computer_drives(computer_name)`: 指定ホストが Issue に登録しているドライブ一覧を返す。
  - `update_issue_body()`: 最新の Issue 本文を再取得してから該当行を差し替え、GitHub API (`PATCH`) で更新（同時実行時の競合を避けるため送信直前に再取得する）。
  - `get_human_readable_size(size)`: バイト数を `B`〜`TB` の人間可読表現に変換。
- **`main()`**: リポジトリ名を環境変数 `GITHUB_REPOSITORY`（未指定時は `book000/book000`）から決定し、`sys.argv[1]` の Issue 番号を検証してから上記フローを実行。結果を `save_results()` で保存する。

### GitHub Issue のデータ形式（重要）

管理対象の行は「Markdown テーブル行 + 末尾の HTML コメントマーカー」で表現されます。マーカーでホスト・ドライブを識別するため、テーブルの表示列だけでは判別しません。

```
| ✅ | hostname1 | C: | 1.20 TB (75.0%) | 1.60 TB (SSD) | <!-- calculate-storage#hostname1#C -->
```

- 行検出の正規表現: `(?P<markdown>.*) <!-- calculate-storage#(?P<computer_name>.+)#(?P<drive>.+) -->`
- サイズ列の正規表現: `^(?P<size>[0-9.]+ [TGMK]B) \((?P<drive_type>.+)\)$`（例: `1.60 TB (SSD)`）
- **マーカー側の `drive` と表示列の `drive` は別物**。マーカーの `drive` 値は `psutil.disk_usage(drive)` に渡される実際の値で、表示列とは異なりうる（上例ではマーカーが `C`、表示列が `C:`。テストも同様: `test_calculate_storage.py`）。
- テーブル部分を `|` で分割すると 7 要素（チェックマーク / computer_name / drive / used / size）になる前提。
- **行の保持挙動（現行実装）**: マーカーの無い行（`row_regex` 不一致）は `update_issue_body()` でそのまま保持される。一方、マーカー付きでも 7 要素に分割できない・サイズ形式が不正な行は `__get_storage_rows()` で `storage_rows` に載らず、`update_issue_body()` の再構成時に**脱落する**。破壊的更新を避けたい場合はマーカー行の形式を厳密に保つこと。

## 認証情報とデータ

- **GitHub トークンはファイルから読む**: `get_github_token()` は `data/github_token.txt` を読み取る。環境変数ではない。このファイルが無い場合は例外で停止する。
- **結果ファイル**: `save_results()` が `results/{hostname}_{YYYYMMDD}.txt` に 1 行 1 JSON（JSON Lines）で書き出す。
- `.gitignore` で `data/` と `results/` を除外済み。トークン・結果ファイルを絶対にコミットしない。ログにトークンや個人情報を出力しない。

## 実装パターン

- **推奨**: 外部依存（GitHub API 通信、`psutil` の戻り値）は `unittest.mock` でモック化してテストする。OS 依存処理は `os.name` で分岐する（例: ホスト名取得は Windows が `COMPUTERNAME`、Unix が `os.uname()`）。
- **非推奨**: 認証情報のハードコード。モックなしの外部通信テスト。OS 判定を伴わないプラットフォーム依存コードの無条件実行。

## テスト

- フレームワークは unittest（標準ライブラリ）。テストは `test_calculate_storage.py`。
- 実行: `python -m unittest discover -s . -p "test_*.py"`。
- 以下の変更時はテストを追加/更新する: 新機能、GitHub API 通信ロジック、ディスク情報取得ロジック、エラーハンドリング、Windows/Unix 両対応が必要な処理。

## ドキュメント更新ルール

- 依存パッケージを変えたら `requirements.txt`。
- アーキテクチャ・実装パターン・データ形式を変えたら本ファイル（`CLAUDE.md`）。
- レビュー観点や規約を変えたら `.github/copilot-instructions.md`。

## 運用上の注意

- **GitHub リポジトリ調査**: 調査目的でリポジトリを参照する場合はテンポラリディレクトリに `git clone` してから検索する。
- **Renovate PR**: Renovate が作成した PR に追加コミット・更新をしない。
- **プルリクエスト**: 作成はユーザーから依頼されたときのみ。作成前にセンシティブ情報が無いこととコンフリクトが無いことを確認する。
