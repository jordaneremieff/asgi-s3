# asgi-s3

<a href="https://pypi.org/project/asgi-s3/">
    <img src="https://badge.fury.io/py/asgi-s3.svg" alt="Package version">
</a>
<a href="https://travis-ci.org/erm/asgi-s3">
    <img src="https://travis-ci.org/erm/asgi-s3.svg?branch=master" alt="Build Status">
</a>


Staticfile management tools and [ASGI](https://asgi.readthedocs.io/en/latest/) middleware support for [Amazon S3](https://aws.amazon.com/s3/). 

**Work in Progress**: A lot of what is here currently will be changing.

## CLI

`s3 sync`

...todo

## Middleware

The middleware is designed to work with any ASGI application. Here is raw ASGI example:

```python

from asgi_s3.middleware import S3StorageMiddleware

async def app(scope, receive, send):
    url_for = scope["asgi_s3"]["url_for"]
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


app = S3StorageMiddleware(
    app,
    bucket_name="my-bucket",
    static_dir="path/to/static/files",
)
```

And here is an example using [Starlette](https://www.starlette.io/):

```python
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates

from asgi_s3.middleware import S3StorageMiddleware

templates = Jinja2Templates("templates")
app = Starlette()

@app.route("/")
def homepage(request):
    s3_url_for = request.scope["asgi_s3"]["s3_url_for"]
    return templates.TemplateResponse(
        "index.html", {"request": request, "s3_url_for": s3_url_for}
    )


app.add_middleware(
    S3StorageMiddleware,
    bucket_name="my-bucket",
    static_dir="path/to/static/files",
)
```

