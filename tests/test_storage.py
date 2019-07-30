import mock
import os
import boto3
from moto import mock_s3

from asgi_s3.storage import S3Storage


@mock_s3
def test_storage(tmpdir) -> S3Storage:
    region_name = "ap-southeast-1"
    bucket_name = "my-bucket"
    static_dir = "static"

    # Create mock bucket
    s3_client = boto3.client("s3")
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": region_name},
    )

    # Create temporary directory and files for testing main storage class
    static_dir = tmpdir.mkdir("static")

    # CSS
    css_content = "body {background-color: red;}"
    css_dir = static_dir.mkdir("css")
    mock_file_one = css_dir.join("style.css")
    mock_file_one.write(css_content)
    assert mock_file_one.read() == css_content

    # JS
    js_content_one = "function test() {console.log('test')}"
    js_dir = static_dir.mkdir("js")
    mock_js_file_one = js_dir.join("index.js")
    mock_js_file_one.write(js_content_one)
    js_content_two = "function test2() {console.log('test2')}"
    assert mock_js_file_one.read() == js_content_one
    mock_js_file_two = js_dir.join("other.js")
    mock_js_file_two.write(js_content_two)
    assert mock_js_file_two.read() == js_content_two

    # Construct storage instance using mock bucket and temporary static directory
    storage = S3Storage(bucket_name, static_dir)
    assert list(storage.local_files.keys()) == [
        "css/style.css",
        "js/other.js",
        "js/index.js",
    ]
    assert storage.remote_files == {}

    # Run the sync operation and ensure the remote files are now populated
    storage.sync()
    storage.init_files()
    assert list(storage.remote_files.keys()) == [
        "css/style.css",
        "js/index.js",
        "js/other.js",
    ]
    assert (
        storage.url_for("css/style.css")
        == f"https://{bucket_name}.s3.amazonaws.com/css/style.css"
    )

    # Test deleting files
    os.remove(mock_js_file_two)
    storage.init_files()
    storage.sync()
    storage.init_files()
    assert list(storage.remote_files.keys()) == ["css/style.css", "js/index.js"]
