import typing
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse

import boto3


class RemoteFile:
    def __init__(self, obj: dict) -> None:
        self.etag = obj["ETag"]
        self.key = obj["Key"]
        self.last_modified = obj["LastModified"]
        self.owner = obj["Owner"]
        self.size = obj["Size"]
        self.storage_class = obj["StorageClass"]


class LocalFile:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.content_type = mimetypes.guess_type(self.file_path)[0]
        self.remote_file = None


class S3Storage:
    def __init__(self, bucket_name: str, static_dir: str, *args, **kwargs) -> None:
        self.bucket_name = bucket_name
        self.static_dir = static_dir
        self.s3_client = boto3.client("s3")
        self.init_files()

    def init_files(self) -> None:
        self.local_files = self.get_local_files()
        self.remote_files = self.get_remote_files()

    def get_local_files(self) -> typing.Dict[str, LocalFile]:
        local_files = {}
        for root, dirs, files in os.walk(self.static_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                relative_file_path = str(Path(file_path).relative_to(self.static_dir))
                local_files[relative_file_path] = LocalFile(file_path)
        return local_files

    def get_remote_files(self) -> typing.Dict[str, RemoteFile]:
        paginator = self.s3_client.get_paginator("list_objects")
        pages = paginator.paginate(Bucket=self.bucket_name)
        remote_files = {}
        try:
            for page in pages:
                for obj in page["Contents"]:
                    remote_files[obj["Key"]] = RemoteFile(obj)
        except KeyError:
            pass
        return remote_files

    def sync(self) -> None:

        deleted_count = 0
        modified_count = 0
        created_count = 0

        deleted_files = []
        for file_key, remote_file in self.remote_files.items():
            if file_key not in self.local_files.keys():
                deleted_files.append({"Key": file_key})
            else:
                self.local_files[file_key].remote_file = remote_file

        if deleted_files:
            self.s3_client.delete_objects(
                Bucket=self.bucket_name, Delete={"Objects": deleted_files}
            )
            deleted_count = len(deleted_files)

        print("Uploading files..")
        for file_key, local_file in self.local_files.items():
            # Check if the file already exists
            if not local_file.remote_file:
                created_count += 1
            else:
                modified_count += 1

            # TODO: Only re-upload when modified

            self.s3_client.upload_file(
                local_file.file_path,
                Key=file_key,
                Bucket=self.bucket_name,
                ExtraArgs={
                    "ACL": "public-read",
                    "ContentType": local_file.content_type,
                },
            )

        print(f"Deleted: {deleted_count}")
        print(f"Created: {created_count}")
        print(f"Modified: {modified_count}")

    def url_for(self, filename) -> str:
        presigned_url = self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": filename},
            ExpiresIn=100,
        )
        parsed = urlparse(presigned_url)
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return url
