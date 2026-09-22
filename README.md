# mysql-backup-tool

MySQLデータベースを **CSV / SQL(INSERT文) 形式でバックアップし、ZIP圧縮してAWS S3にアップロードする** ためのCLIツール一式です。

アップロードされていた検証用スクリプト（`push_csv&&dump.py`, `sample_restore.py`, `open_zip.py`, `aws_test.py` など）を元に、
処理を関数単位に整理し、リポジトリとして扱いやすい形にまとめています。

## できること

- 対話形式でMySQLに接続（前回入力した接続情報を再利用可能）
- 接続先データベースを選んで、全テーブルを自動検出
- 各テーブルを以下の形式でエクスポート
  - `backup-output/data/<table>.csv`
  - `backup-output/schema/<table>.sql`（INSERT文）
- バックアップ内容を `manifest.json` として記録（テーブル一覧・日時・MySQLバージョン・ファイルサイズ・DB一覧）
- 成果物一式を `backup-output.zip` に圧縮
- 任意でAWS S3（`internship` プロファイル）にアップロード
- `schema/*.sql` からテーブルへ再投入する簡易リストア
- 配布されたZIPを展開するGUIツール（`tkinter`のファイル選択ダイアログ）

## ディレクトリ構成

```
mysql-backup-tool/
├── README.md
├── requirements.txt
├── .gitignore
├── input_data.txt.example      # 接続情報のテンプレート（本物はコミットしない）
├── src/
│   ├── backup.py                # バックアップ本体（CSV/SQL出力 → manifest → ZIP → S3）
│   ├── restore.py               # schema/*.sql からのリストア
│   ├── open_zip.py              # ZIP展開ツール（GUI）
│   └── aws_upload_test.py       # S3アップロードの疎通確認用
├── docs/
│   ├── aws_procedure.md         # AWS CLIコマンド集
│   └── git_workflow.md          # チームでのGit運用ルール
├── sample_data/                 # バックアップ結果のサンプル（users/orders/users_sample）
└── tests/
    └── test_backup.py
```

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate    # Windowsは .venv\Scripts\activate
pip install -r requirements.txt
```

MySQLの接続情報を保存したい場合は `input_data.txt.example` を `input_data.txt` にコピーして編集してください
（`input_data.txt` は `.gitignore` 済みでコミットされません）。

```bash
cp input_data.txt.example input_data.txt
```

AWSへのアップロードを使う場合は、あらかじめ `internship` という名前のAWS CLIプロファイルを設定しておいてください。

```bash
aws configure --profile internship
```

## 使い方

### バックアップを取る

```bash
python src/backup.py
```

対話形式で

1. 前回の接続情報を使うか (y/n)
2. 対象データベースの選択（番号）
3. manifestファイル名
4. S3へアップロードするか (y/n)

を聞かれます。成功すると `backup-output/` 以下にCSV・SQL・manifest.jsonが、
リポジトリ直下に `backup-output.zip` が作成されます。

### リストアする

```bash
python src/restore.py
```

`backup-output/schema/*.sql` にあるINSERT文を、接続先データベースへ再投入します。

### ZIPを展開する

```bash
python src/open_zip.py
```

ファイル選択ダイアログが開くので、展開したいZIPを選択してください。

## サンプルデータについて

`sample_data/` には検証時に作成された `users` / `orders` / `users_sample` テーブルの
CSV・SQLエクスポート結果と `manifest.json` を格納しています。CSVは以下のような
エッジケース（空文字・カンマ入り・ダブルクォート・改行・NULL文字列）を含んでいるため、
エクスポート処理の動作確認用データとして利用できます。

| ファイル | 内容 |
| --- | --- |
| `users.csv` / `users.sql` | ユーザーテーブル（特殊文字を含むテストデータ） |
| `orders.csv` / `orders.sql` | 注文テーブル（大量のサンプル行） |
| `users_sample.csv` / `users_sample.sql` | 空/最小構成のサンプルテーブル |
| `manifest.json` | 上記バックアップ実行時のメタ情報 |

## ドキュメント

- [`docs/aws_procedure.md`](docs/aws_procedure.md) — S3バケット作成・アップロード・削除などのAWS CLIコマンド集
- [`docs/git_workflow.md`](docs/git_workflow.md) — 複数人開発でお互いの変更を消さないためのGit運用手順

## 注意事項

- `src/backup.py` のSQLエクスポートは簡易的なエスケープ（シングルクォートの二重化）のみ行っています。
  本番データや信頼できない入力を扱う場合は、`mysqldump` の利用や、プレースホルダ経由でのエクスポートを検討してください。
- 接続情報（パスワードを含む `input_data.txt`）は絶対にリポジトリにコミットしないでください。
