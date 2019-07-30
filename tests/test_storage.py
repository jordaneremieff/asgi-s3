import boto3
from moto import mock_s3

from asgi_s3.storage import S3Storage, S3Files


@mock_s3
def test_storage() -> None:
    region_name = "us-east-1"
    bucket_name = "my-bucket"
    static_dir = "static"
    conn = boto3.resource("s3", region_name=region_name)
    conn.create_bucket(Bucket=bucket_name)
    storage = S3Storage(bucket_name=bucket_name, static_dir=static_dir)
    static_files = S3Files(storage=storage)
    print(static_files)
