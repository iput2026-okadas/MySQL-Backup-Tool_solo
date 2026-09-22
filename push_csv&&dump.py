"""
MySQLデータベースのバックアップを取得するツール。

全テーブルを自動取得し、
・CSVファイル出力
・SQLファイル出力
・バックアップ情報(JSON)作成
・ZIP圧縮
を実行する。

テーブル名を直接指定する必要はなく、
取得したテーブル一覧を利用して自動でバックアップを行う。
"""

import mysql.connector
from mysql.connector import Error
import csv
import os
from pathlib import Path
from datetime import datetime
import json
import shutil
import zipfile
import time
import boto3
import unicodedata


#本人のデータに合わせる
# プレイヤーに接続情報を入力させる
print("--- MySQLの接続情報を入力してください ---")

while True:
    d = input("前回使用したデータを使用しますか？ (y/n): ").lower()
    d = unicodedata.normalize("NFKC", d).lower()
    if d in ["y", "n"]:
        break
    print("y か n を入力してください")
    
CONFIG_FILE = Path(__file__).resolve().parent / "input_data.txt"
if d=='n':

        config = {
                'host': input("ホスト名 (例: localhost): ") or "localhost",
                'user': input("ユーザー名(例:root): ")or"root",
                'password': input("パスワード: "),
                'charset': input("型指定(例:utf8mb4): ")or "utf8mb4"
            }
        while True:
            reg = input("次回の登録を簡略化するために登録しますか？ (y/n): ")
            reg = unicodedata.normalize("NFKC", reg).lower()

            if reg in ["y", "n"]:
                break
            print("y か n を入力してください")
        if reg == 'y':
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(
                    f"{config['host']}\n"
                    f"{config['user']}\n"
                    f"{config['password']}\n"
                    f"{config['charset']}\n"
                )
            print("登録しました。"'\n'f"保存先: {CONFIG_FILE}")
        else:
            print("登録キャンセルしました。")
    
else:
       with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines()]
                config = {
                            'host': lines[0],
                            'user': lines[1],
                            'password': lines[2],
                            'charset': lines[3]
                            }

try:
    print("\nデータベースに接続中...")
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # 接続確認用のテストクエリ
    cursor.execute("SELECT VERSION()")
    print("成功! MySQL Version:", cursor.fetchone()[0]+"\n")
    
except mysql.connector.Error as err:
    print(f"\n[エラー] 接続に失敗しました: {err}")
finally:
    if 'cursor' in locals() and cursor:
        cursor.close()
    if 'conn' in locals() and conn.is_connected():
        conn.close()

try:
    
# ジェネレータ
    def iter_row_batches(
        connection,
        table_name: str,
        batch_size: int = 2
    ):
        cursor = connection.cursor()

        try:
            cursor.execute(f"SELECT * FROM {table_name};")

            while True:
                batch = cursor.fetchmany(batch_size)

                if not batch:
                    break

                print(f"{len(batch)}件取得")
                #time.sleep(1)
                yield batch

        finally:
            cursor.close()

    try:
        # 接続
        connection = mysql.connector.connect(**config)
        tables_list = []
        if connection.is_connected():
            print("接続できました。")

        cursor = connection.cursor()

        # データベース一覧取得

        cursor.execute("SHOW DATABASES;")

        databases = cursor.fetchall()
        print("=== データベース一覧 ===")
        for i, db in enumerate(databases, start=1):
            print(f"\033[31m{i}\033[0m {db[0]}")

        choice = int(input("使用するデータベース"+'\033[31m'+"番号"+'\033[0m'+"を入力してください:"))  #('\033[31m'+'赤色'+'\033[0m')
        selected_db = databases[choice - 1][0]
        # データベース切替
        cursor.execute(f"USE `{selected_db}`")
        print(f"\n選択したデータベース: {selected_db}")
       
        
        # テーブル名を指定
        for batch in iter_row_batches(
            connection,
            table_name="orders",
            batch_size=10
        ):
            for row in batch:
                print(row)

        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

            
        for table in tables:
                tables_list.append(table[0])
                print("テーブル名:", table[0]+"\n")
        cursor.close()

    except Error as e:
        print("ここでエラー")
        print(e)


    #テーブル指定を自動化するためにリストを使
    # 用し割り当てる
    tables_numbers = len(tables_list)
    
    # スクリプトの場所を基準にする
    BASE_DIR = Path(__file__).resolve().parent.parent
    OUTPUT_DIR = BASE_DIR / "backup-output2"
    DATA_DIR = OUTPUT_DIR / "data"
    SCHEMA_DIR = OUTPUT_DIR / "schema"

    # フォルダが無ければ作成
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    #カラム一覧表示
    for i in range(len(tables_list)):
        cursor = connection.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {tables_list[i]};")
        columns = cursor.fetchall()
        print(f"{tables_list[i]}のカラム一覧:")
        for column in columns:
            print(column[0])

        cursor.close()


    # csvファイルに書き込み
    counter=0
    i=len(batch)    
    for i in range(len(tables_list)):
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {tables_list[i]};")
        
        with open(DATA_DIR / f"{tables_list[i]}.csv",'w',newline='',encoding='utf-8') as csvfile:
           
            writer = csv.writer(csvfile)

            writer.writerow([p[0] for p in cursor.description])

            for row in cursor:
                    #ここに10件ごとにcsv化
                    counter=counter+1
                    writer.writerow(row)
                    
                    #time.sleep(1)
                    print(f"{tables_list[i]}テーブルのデータをCSVファイルに書き込みました。")
                    #ここにzip化するコードを作成する
            print(counter)   
        cursor.close()

    #mysqldump保存
    for table in tables_list:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table};")

        sql_path = SCHEMA_DIR / f"{table}.sql"

        with open(sql_path, "w", encoding="utf-8") as sqlfile:
            for row in cursor:
                values = []

                for value in row:
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        values.append(f"'{value}'")
                    else:
                        values.append(str(value))

                sql = (f"INSERT INTO {table} VALUES "f"({', '.join(values)});\n")

                sqlfile.write(sql)
      
        print(f"{table}.sql を作成しました")
    

except Error as e:
    print("ここでエラー")
    raise


# jsonファイルに書き込み
"""
以下、バックアップの内容を説明するためのjsonファイルを作成するコード
"""
#データベース一覧表示

cursor = connection.cursor()
cursor.execute("SHOW DATABASES;")
databases = cursor.fetchall()
cursor.close()
print("データベース一覧:")
for database in databases:
    print(database[0])


# MySQLのバージョン取得
cursor = connection.cursor()
cursor.execute("SELECT VERSION();")
version = cursor.fetchone()

print("MySQL Version:", version[0],"\n")
    
#バックアップ情報を格納する辞書を作成
backup_info = {
    "テーブルリスト": tables_list,
    "バックアップ日時:": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "MySQL Version": "MySQL Version: "+version[0] ,
    "ファイルサイズ": {f"{table}.csv": f"{os.path.getsize(Path(__file__).parent.parent / 'backup-output2' / 'data' / f'{table}.csv')} bytes"for table in tables_list },
    "データベース一覧": [database[0] for database in databases],
}

#jsonファイルに書き込み
Jsona=input("jsonファイルの名称を決めてください")or "manifest.json"
with open(OUTPUT_DIR / Jsona, "w",encoding="utf-8") as jsonfile:
    json.dump(backup_info, jsonfile, ensure_ascii=False, indent=4)

print("jsonファイル名は"+Jsona+"です。"+"\n"+"バックアップ情報をJSONファイルに書き込みました。"+"\n")


#zip化

def zip_directory(source_dir, output_zip):
    """
    :param source_dir: 圧縮したいディレクトリのパス
    :param output_zip: 出力ZIPファイルのパス
    """
    if not os.path.isdir(source_dir):
        raise ValueError(f"指定されたパスがディレクトリではありません: {source_dir}")

    # shutil.make_archiveは拡張子を自動で付与するらしい
    shutil.make_archive(output_zip, 'zip', root_dir=source_dir)
    print(f"ZIPファイルを作成しました: {output_zip}.zip"+"\n")


#csv
directory_csv_path = str(OUTPUT_DIR)

zip_file_csv_path = str(BASE_DIR / "backup-output")

print(zip_file_csv_path+"がパス")

try:
    zip_directory( directory_csv_path,zip_file_csv_path )

except Error as e:
    print(f"エラー: {e}")


#aws
#パケット自動生成機能ほしい　日程固定かな
session = boto3.Session(
    profile_name="internship",
    region_name="ap-northeast-1"
)

s3 = session.resource("s3")

you_Bucket=input("バケットを選択してください:")or"ssg-test-bucket-20260914"
print("\n"+"名称は"+you_Bucket+"です")

with open("backup-output.zip", "rb") as data:
    s3.Bucket(you_Bucket).put_object(
        Key="backup-output2.zip",
        Body=data
    )

print("AWSにアップロード成功しました。"+"\n"+"送信したバケットは"+you_Bucket+"です。")