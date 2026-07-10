# GitHub Copilot コードレビュー指示

calculate-storage は、GitHub Issue の Markdown テーブルを複数マシンのディスク使用量ダッシュボードとして更新する Python ツール（単一ファイル `calculate_storage.py`）です。以下の観点でレビューしてください。

## 強制されている規約

- コメント・docstring・レビューコメントは日本語。エラーメッセージ / ログメッセージは英語。
- 日本語と英数字の間には半角スペースを入れる。これが欠けている箇所は指摘してよい。
- インデントはスペース 2 個（Python も 2）。改行 LF、UTF-8、末尾改行あり（`.editorconfig`）。逸脱を指摘する。
- 命名: クラス PascalCase、関数・変数 snake_case、定数 UPPER_SNAKE_CASE。
- 公開関数・クラスには日本語 docstring を求める。
- コミットは Conventional Commits（description は日本語）。

## 重点的に確認すべき点

- **Issue 本文の破壊的更新**: 行は `<!-- calculate-storage#computer_name#drive -->` マーカーで識別する。マーカーの無い行や形式が合わない行は必ずそのまま保持すること。この保持ロジックを壊す変更（無条件の行削除・並べ替え・マーカー欠落）は重大な指摘対象。
- **正規表現の整合性**: 行検出 `(?P<markdown>.*) <!-- calculate-storage#(?P<computer_name>.+)#(?P<drive>.+) -->` とサイズ `^(?P<size>[0-9.]+ [TGMK]B) \((?P<drive_type>.+)\)$` を変える場合、双方向（解析と再生成）の整合が取れているか確認する。
- **認証情報**: トークンは `data/github_token.txt` から読む。トークンや Issue 本文をログ・例外メッセージ・コミットに露出させていないか。`data/` `results/` 配下をコミットに含めていないか。
- **エラーハンドリング**: GitHub API 呼び出し（非 200 応答）、`psutil.disk_usage` の `OSError`、ログ/結果ディレクトリ作成失敗が握り潰されず適切に処理・記録されているか。
- **OS 依存処理**: ホスト名取得やパスなど OS 分岐（`os.name`）が Windows/Unix 双方で成立するか。片側のみで壊れる変更を指摘する。
- **テスト**: ロジック変更に対応する unittest があるか。GitHub API・psutil などの外部依存は `unittest.mock` でモック化されているか（実ネットワーク通信を伴うテストは指摘対象）。CI は Python 3.9〜3.13 マトリックスのため、新しい構文/API が 3.9 で動くか確認する。

## 誤検知しやすい（フラグ不要な）パターン

- インデントが 2 スペースなのは仕様（PEP 8 の 4 スペースからの逸脱を指摘しない）。
- `data/github_token.txt` からのトークン読み込みは意図的な設計。「環境変数を使え」という一般論は不要。
- `GitHubIssue` の名前二重アンダースコアメソッド（`__get_issue_body` 等）は意図的な非公開メソッド。
- 結果ファイルの拡張子が `.txt` で中身が JSON Lines なのは既存仕様。
