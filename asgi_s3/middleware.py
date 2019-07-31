from contextvars import ContextVar


from asgi_s3.storage import S3Storage


s3_storage = ContextVar("s3_storage")


class S3StorageMiddleware:
    def __init__(
        self,
        app,
        bucket_name: str,
        static_dir: str,
        region_name: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
    ) -> None:
        self.app = app
        s3_storage.set(
            S3Storage(
                bucket_name=bucket_name,
                static_dir=static_dir,
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
        )

    async def __call__(self, scope, receive, send):
        try:
            await self.app(scope, receive, send)
        except BaseException as exc:  # pragma: no cover
            raise exc


def s3_url_for(filename: str) -> str:
    _s3_storage = s3_storage.get()
    return _s3_storage.s3_url_for(filename)
