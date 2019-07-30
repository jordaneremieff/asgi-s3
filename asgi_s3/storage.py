import boto3
import mimetypes
import os
from pathlib import Path


class S3Storage:
    def __init__(self, bucket_name: str, static_dir: str, *args, **kwargs) -> None:
        self.bucket_name = bucket_name
        self.static_dir = static_dir
        self.s3_client = boto3.client("s3")
        self.remote_files = self.get_remote_files()
        self.local_files = self.get_local_files()
        self.deleted_files = [
            {"Key": i} for i in self.remote_files if i not in self.local_files
        ]

    def get_local_files(self) -> list:
        local_files = []
        for root, dirs, files in os.walk(self.static_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                relative_file_path = str(Path(file_path).relative_to(self.static_dir))
                local_files.append(relative_file_path)
        return local_files

    def get_remote_files(self) -> list:
        paginator = self.s3_client.get_paginator("list_objects")
        pages = paginator.paginate(Bucket=self.bucket_name)
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
            response = self.s3_client.delete_objects(
                Bucket=self.bucket_name, Delete={"Objects": self.deleted_files}
            )
            print(response)

        print("Uploading files..")
        for file in self.local_files:
            file_path = os.path.join(self.static_dir, file)
            relative_file_path = str(Path(file_path).relative_to(self.static_dir))
            content_type = mimetypes.guess_type(file_path)[0]
            response = self.s3_client.upload_file(
                file_path,
                Key=relative_file_path,
                Bucket=self.bucket_name,
                ExtraArgs={"ACL": "public-read", "ContentType": content_type},
            )
            print(response)
