import boto3
import mimetypes
import os
from pathlib import Path


class S3Storage:
    def __init__(self, bucket_name: str, static_dir: str, *args, **kwargs) -> None:
        self.bucket_name = bucket_name
        self.static_dir = static_dir
        self.s3_client = boto3.client("s3")

    def sync(self) -> None:
        static_files = S3Files(storage=self)
        static_files.sync_files()


class S3Files:
    def __init__(self, *, storage: S3Storage) -> None:
        self.storage = storage
        self.remote_files = self.get_remote_files()
        self.local_files = self.get_local_files()
        self.deleted_files = [
            {"Key": i} for i in self.remote_files if i not in self.local_files
        ]

    def get_local_files(self) -> list:
        local_files = []
        for root, dirs, files in os.walk(self.storage.static_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                relative_file_path = str(
                    Path(file_path).relative_to(self.storage.static_dir)
                )
                local_files.append(relative_file_path)
        return local_files

    def get_remote_files(self) -> list:
        paginator = self.storage.s3_client.get_paginator("list_objects")
        pages = paginator.paginate(Bucket=self.storage.bucket_name)
        remote_files = []
        try:
            for page in pages:
                for obj in page["Contents"]:
                    remote_files.append(obj["Key"])
        except KeyError:
            pass
        return remote_files

    def sync_files(self) -> None:
        if self.deleted_files:
            print("Deleting missing files..")
            response = self.storage.s3_client.delete_objects(
                Bucket=self.storage.bucket_name, Delete={"Objects": self.deleted_files}
            )
            print(response)

        print("Uploading files..")
        for file in self.local_files:
            file_path = os.path.join(self.storage.static_dir, file)
            relative_file_path = str(
                Path(file_path).relative_to(self.storage.static_dir)
            )
            content_type = mimetypes.guess_type(file_path)[0]
            response = self.storage.s3_client.upload_file(
                file_path,
                Key=relative_file_path,
                Bucket=self.storage.bucket_name,
                ExtraArgs={"ACL": "public-read", "ContentType": content_type},
            )
            print(response)
