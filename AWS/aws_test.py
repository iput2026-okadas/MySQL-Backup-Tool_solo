"""
awsのアップロード確認用
"""

import boto3
import boto3

session = boto3.Session(
    profile_name="internship",
    region_name="ap-northeast-1"
)

s3 = session.resource("s3")

with open("aws_sample_upload.txt", "rb") as data:
    s3.Bucket("ssg-test-bucket-20260911").put_object(
        Key="aws_sample_upload.txt",
        Body=data
    )

print("アップロード成功")