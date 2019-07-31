import boto3
from moto import mock_s3
from click.testing import CliRunner

from asgi_s3.cli import create_bucket, list_buckets  # , sync_bucket


@mock_s3
def test_cli() -> None:
    region_name = "ap-southeast-1"
    bucket_name = "my-bucket"
    runner = CliRunner()
    result = runner.invoke(create_bucket, [bucket_name, region_name])
    assert result.exit_code == 0
    assert result.output == "Bucket created! Bucket: my-bucket Region: ap-southeast-1\n"


@mock_s3
def test_cli_bucket_exists() -> None:
    region_name = "ap-southeast-1"
    bucket_name = "my-bucket"
    s3_client = boto3.client("s3")
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": region_name},
    )
    runner = CliRunner()
    result = runner.invoke(create_bucket, [bucket_name, region_name])
    assert (
        result.output
        == "Error: An error occurred (BucketAlreadyExists) when calling the CreateBucket operation: The requested bucket name is not available. The bucket namespace is shared by all users of the system. Please select a different name and try again\n"
    )


@mock_s3
def test_cli_bucket_defaults() -> None:
    runner = CliRunner()
    result = runner.invoke(create_bucket, [])
    assert "No bucket name provided, one will be generated." in result.output
    assert "No region specified, using default." in result.output
    assert "Bucket created!" in result.output


@mock_s3
def test_cli_list_buckets() -> None:
    region_name = "ap-southeast-1"
    bucket_name = "my-bucket"
    bucket_name_two = "my-bucket-2"
    s3_client = boto3.client("s3")
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": region_name},
    )
    s3_client.create_bucket(
        Bucket=bucket_name_two,
        CreateBucketConfiguration={"LocationConstraint": region_name},
    )
    runner = CliRunner()
    result = runner.invoke(list_buckets, [])
    assert result.output == "['my-bucket', 'my-bucket-2']\n"


# @mock_s3
# def test_cli_sync() -> None:
#     region_name = "ap-southeast-1"
#     bucket_name = "my-bucket"
#     static_dir = "static"
#     s3_client = boto3.client("s3")
#     s3_client.create_bucket(
#         Bucket=bucket_name,
#         CreateBucketConfiguration={"LocationConstraint": region_name},
#     )
#     runner = CliRunner()
#     result = runner.invoke(sync_bucket, [bucket_name, static_dir])
