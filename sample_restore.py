import mysql.connector
from mysql.connector import Error
from collections.abc import Iterator
from typing import Any

# 接続設定
config = {
    "host": "localhost",
    "user": "root",
    "password": "0426",
    "charset": "utf8mb4"
}

Row = tuple[Any, ...]
RowBatch = list[Row]


# ジェネレータ
def iter_row_batches(
    connection,
    table_name: str,
    batch_size: int = 1
):
    cursor = connection.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table_name};")

        while True:
            batch = cursor.fetchmany(batch_size)

            if not batch:
                break

            print(f"{len(batch)}件取得")
            yield batch

    finally:
        cursor.close()
        cursor.close()

try:
    # 接続
    connection = mysql.connector.connect(**config)

    if connection.is_connected():
        print("接続できました。")

    cursor = connection.cursor()
    cursor.execute("USE backup_test;")

    # テーブル名を指定
    for batch in iter_row_batches(
        connection,
        table_name="orders",
        batch_size=3
    ):
        for row in batch:
            print(row)

except Error as e:
    print("ここでエラー")
    print(e)

finally:
    if "connection" in locals() and connection.is_connected():
        connection.close()
        print("接続を閉じました。")