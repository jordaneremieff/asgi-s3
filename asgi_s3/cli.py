import boto3
import click
import uuid
from botocore.exceptions import ClientError


from asgi_s3.storage import S3Storage, S3Config


@click.group()  # pragma: no cover
def s3() -> None:
    pass


@s3.command()
@click.argument("bucket_name", required=False)
@click.argument("region_name", required=False)
def create_bucket(bucket_name: str, region_name: str) -> None:
    """
    Create a new S3 bucket.
    """

    if not bucket_name:
        click.echo("No bucket name provided, one will be generated.")
        bucket_name = f"asgi-s3-{uuid.uuid4()}"

    if not region_name:
        click.echo(f"No region specified, using default.")

    config = S3Config(bucket_name=bucket_name, region_name=region_name)

    try:
        config.client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": config.region_name},
        )
    except ClientError as exc:
        click.echo(f"Error: {exc}")
    else:
        click.echo(
            f"Bucket created! Bucket: {config.bucket_name} Region: {config.region_name}"
        )


@s3.command()
@click.argument("bucket_name")
@click.argument("static_dir")
def sync_bucket(bucket_name: str, static_dir: str) -> None:  # pragma: no cover
    """
    Sync a bucket with a local static file directory.
    """
    storage = S3Storage(bucket_name=bucket_name, static_dir=static_dir)
    storage.sync()


@s3.command()
def list_buckets() -> None:
    """
    List all S3 buckets.
    """
    s3_client = boto3.client("s3")
    response = s3_client.list_buckets()
    buckets = [bucket["Name"] for bucket in response["Buckets"]]
    click.echo(buckets)


# @s3.command()
# @click.argument("bucket_name")
# def info(bucket_name: str) -> None:
#     s3_client = boto3.client("s3")
#     response = s3_client.list_objects_v2(Bucket=bucket_name)
#     key_count = response["KeyCount"]
#     click.echo(f"Bucket '{bucket_name}' contains {key_count} files")
