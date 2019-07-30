import boto3
from moto import mock_s3

from starlette.responses import HTMLResponse
from starlette.testclient import TestClient
from starlette.applications import Starlette


from asgi_s3.middleware import S3StorageMiddleware


@mock_s3
def test_middleware() -> None:

    region_name = "us-east-1"
    bucket_name = "my-bucket"
    static_dir = "static"
    conn = boto3.resource("s3", region_name=region_name)
    conn.create_bucket(Bucket=bucket_name)

    async def app(scope, receive, send):
        url_for = scope["asgi_s3"]["s3_url_for"]
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"text/html; charset=utf-8"]],
            }
        )
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ASGI S3 example</title>
            <link rel="stylesheet" href="{url_for('style.css')}">
        </head>
        <body>
        Hello, world.
        </body>
        </html>
        """
        await send({"type": "http.response.body", "body": html_content.encode()})

    app = S3StorageMiddleware(app, bucket_name=bucket_name, static_dir=static_dir)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert (
        response.text
        == """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ASGI S3 example</title>
            <link rel="stylesheet" href="https://my-bucket.s3.amazonaws.com/style.css">
        </head>
        <body>
        Hello, world.
        </body>
        </html>
        """
    )

    app = Starlette()

    @app.route("/")
    async def home(request):
        s3_url_for = request.scope["asgi_s3"]["s3_url_for"]
        url = s3_url_for("style.css")
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ASGI S3 example</title>
            <link rel="stylesheet" href="{url}">
        </head>
        <body>
        Hello, world.
        </body>
        </html>
        """
        return HTMLResponse(html_content)

    app.add_middleware(
        S3StorageMiddleware, bucket_name=bucket_name, static_dir=static_dir
    )

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert (
        response.text
        == """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ASGI S3 example</title>
            <link rel="stylesheet" href="https://my-bucket.s3.amazonaws.com/style.css">
        </head>
        <body>
        Hello, world.
        </body>
        </html>
        """
    )
