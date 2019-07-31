import pytest
import boto3


class MockStorageContext:
    def __init__(
        self, bucket_name="my-bucket", region_name: str = "ap-southeast-1"
    ) -> None:
        self.bucket_name = bucket_name
        self.region_name = region_name
        client = boto3.client("s3")
        client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={"LocationConstraint": self.region_name},
        )


@pytest.fixture
def mock_storage_context() -> MockStorageContext:
    return MockStorageContext
