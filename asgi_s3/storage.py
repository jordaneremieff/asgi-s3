import typing
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse

import boto3


class S3Config:
    """
    Configuration for S3, attempts to retrieve defaults if not provided.
    """

    def __init__(
        self,
        bucket_name: str,
        region_name: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
    ) -> None:

        if None in (region_name, aws_access_key_id, aws_secret_access_key):
            session = boto3.session.Session()

            if region_name is None:
                region_name = session.region_name

            if aws_access_key_id is None or aws_secret_access_key is None:
                credentials = session.get_credentials()
                credentials = credentials.get_frozen_credentials()
                aws_access_key_id = credentials.access_key
                aws_secret_access_key = credentials.secret_key

        self.bucket_name = bucket_name
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.client = boto3.client("s3")


class S3File:
    """
    Represents both a local and remote file.
    """

    def __init__(
        self, local_file_path: str = None, remote_file_object: dict = None
    ) -> None:
        self.remote_file_object = remote_file_object or {}
        self.local_file_path = local_file_path

    @property
    def content_type(self) -> str:  # pragma: no cover
        if self.local_file_path:
            return mimetypes.guess_type(self.local_file_path)[0]
        return None

    @property
    def has_remote_file(self) -> bool:
        return bool(self.remote_file_object)

    @property
    def is_deleted(self) -> bool:
        return self.local_file_path is None

    @property
    def etag(self) -> str:
        return self.remote_file_object.get("ETag")

    @property
    def key(self) -> str:
        return self.remote_file_object.get("Key")

    @property
    def last_modified(self) -> str:
        return self.remote_file_object.get("LastModified")

    @property
    def owner(self) -> str:
        return self.remote_file_object.get("Owner")

    @property
    def size(self) -> str:
        return self.remote_file_object.get("Size")

    @property
    def storage_class(self):
        return self.remote_file_object.get("StorageClass")


class S3Storage:
    """
    Main storage class that handles gathering and syncing files.
    """

    def __init__(
        self,
        bucket_name: str,
        static_dir: str,
        region_name: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
    ) -> None:
        self.config = S3Config(
            bucket_name=bucket_name,
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.static_dir = static_dir
        self.files = self.get_files()

    def get_files(self) -> typing.Dict[str, S3File]:

        s3_file_objects = {}
        s3_files = {}

        paginator = self.config.client.get_paginator("list_objects")
        pages = paginator.paginate(Bucket=self.config.bucket_name)

        try:
            for page in pages:
                for s3_obj in page["Contents"]:
                    s3_file_objects[s3_obj["Key"]] = s3_obj
        except KeyError:
            pass

        for root, dirs, files in os.walk(self.static_dir):
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                relative_file_path = str(
                    Path(local_file_path).relative_to(self.static_dir)
                )
                s3_file_object = s3_file_objects.pop(relative_file_path, None)
                s3_files[relative_file_path] = S3File(
                    local_file_path, remote_file_object=s3_file_object
                )

        if len(s3_file_objects):
            # If any remote S3 files remain after associating them with local files,
            # then they will be deleted after the next sync operation by checking if
            # a local file path is defined.
            for s3_key, s3_obj in s3_file_objects.items():
                s3_files[s3_key] = S3File(
                    local_file_path=None, remote_file_object=s3_file_object
                )

        return s3_files

    def sync(self) -> None:

        deleted_count = 0
        modified_count = 0
        created_count = 0

        deleted_files = []
        for s3_key, s3_file in self.files.items():
            if s3_file.is_deleted:
                deleted_files.append({"Key": s3_key})

        if deleted_files:
            self.config.client.delete_objects(
                Bucket=self.config.bucket_name, Delete={"Objects": deleted_files}
            )
            deleted_count = len(deleted_files)

        for s3_key, s3_file in self.files.items():
            # Check if the file already exists
            if not s3_file.has_remote_file:
                created_count += 1
            else:
                modified_count += 1

            if not s3_file.is_deleted:

                self.config.client.upload_file(
                    s3_file.local_file_path,
                    Key=s3_key,
                    Bucket=self.config.bucket_name,
                    ExtraArgs={
                        "ACL": "public-read",
                        "ContentType": s3_file.content_type,
                    },
                )

        print(f"Deleted: {deleted_count}")
        print(f"Created: {created_count}")
        print(f"Modified: {modified_count}")

    def s3_url_for(self, filename: str) -> str:

        presigned_url = self.config.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.config.bucket_name, "Key": filename},
            ExpiresIn=100,
        )
        parsed = urlparse(presigned_url)
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return url
