from urllib.parse import urlparse

from asgi_s3.storage import S3Storage


class S3StorageMiddleware:
    def __init__(self, app, bucket_name: str, static_dir: str) -> None:
        self.app = app
        self.storage = S3Storage(bucket_name, static_dir)

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope["asgi_s3"] = {"s3_url_for": self.s3_url_for}
        try:
            await self.app(scope, receive, send)
        except BaseException as exc:  # pragma: no cover
            raise exc

    def s3_url_for(self, filename: str) -> str:
        presigned_url = self.storage.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.storage.bucket_name, "Key": filename},
            ExpiresIn=100,
        )
        parsed = urlparse(presigned_url)
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return url
