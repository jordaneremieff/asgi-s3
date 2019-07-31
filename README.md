# asgi-s3

<a href="https://pypi.org/project/asgi-s3/">
    <img src="https://badge.fury.io/py/asgi-s3.svg" alt="Package version">
</a>
<a href="https://travis-ci.org/erm/asgi-s3">
    <img src="https://travis-ci.org/erm/asgi-s3.svg?branch=master" alt="Build Status">
</a>


Static file management tools and [ASGI](https://asgi.readthedocs.io/en/latest/) middleware support for [Amazon S3](https://aws.amazon.com/s3/). 

**Work in Progress**: A lot of what is here currently will be changing, not recommended for any serious usage at this point.

**Requirements**: Python 3.6+

## Installation

```shell
pip install asgi-s3
```

...but you probably just want to clone the `master` branch for the moment.

## CLI

```shell
s3 create-bucket  Create a new S3 bucket.

s3 list-buckets   List all S3 buckets.

s3 sync-bucket    Sync a bucket with a local static file directory.
```

...todo

## Middleware

The middleware is designed to work with any ASGI application. Here is raw ASGI example:

```python
from asgi_s3.middleware import S3StorageMiddleware, s3_url_for


AWS_ACCESS_KEY_ID = "access-key-id"
AWS_SECRET_ACCESS_KEY = "secret-access-key"
BUCKET_NAME = "my-bucket"
REGION_NAME = "region-name"
STATIC_DIR = "path/to/static/files"


async def app(scope, receive, send):
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
        <link rel="stylesheet" href="{s3_url_for('style.css')}">
    </head>
    <body>
    Hello, world.
    </body>
    </html>
    """
    await send({"type": "http.response.body", "body": html_content.encode()})


app = S3StorageMiddleware(
    app,
    bucket_name=BUCKET_NAME,
    static_dir=STATIC_DIR,
    region_name=REGION_NAME,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)
```

And here is an example using [Starlette](https://www.starlette.io/):

```python
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates

from asgi_s3.middleware import S3StorageMiddleware, s3_url_for


templates = Jinja2Templates("templates")
app = Starlette()

@app.route("/")
def homepage(request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "s3_url_for": s3_url_for}
    )


AWS_ACCESS_KEY_ID = "access-key-id"
AWS_SECRET_ACCESS_KEY = "secret-access-key"
BUCKET_NAME = "my-bucket"
REGION_NAME = "region-name"
STATIC_DIR = "path/to/static/files"


app.add_middleware(
    S3StorageMiddleware,
    bucket_name=BUCKET_NAME,
    static_dir=STATIC_DIR,
    region_name=REGION_NAME,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)
```

