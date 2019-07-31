import os

from moto import mock_s3

from asgi_s3.storage import S3Storage


@mock_s3
def test_storage(mock_storage_context, tmpdir) -> S3Storage:

    context = mock_storage_context()

    # Create temporary directory and files for testing main storage class
    static_dir = tmpdir.mkdir("static")

    # Create one temporary CSS file
    css_content = "body {background-color: red;}"
    css_dir = static_dir.mkdir("css")
    mock_file_one = css_dir.join("style.css")
    mock_file_one.write(css_content)
    assert mock_file_one.read() == css_content

    # Create two temporary JS files
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
    storage = S3Storage(context.bucket_name, static_dir)

    mock_files = ["css/style.css", "js/other.js", "js/index.js"]

    for file_name in mock_files:
        file = storage.files.get(file_name)
        assert file is not None
        assert not file.has_remote_file
        assert not file.etag
        assert not file.key
        assert not file.last_modified
        assert not file.owner
        assert not file.size
        assert not file.storage_class

    # Run the sync operation and ensure the remote files are now populated
    storage.sync()
    storage.files = storage.get_files()

    for file_name in mock_files:
        file = storage.files.get(file_name)
        assert file is not None
        assert file.has_remote_file

    assert (
        storage.s3_url_for("css/style.css")
        == f"https://{context.bucket_name}.s3.amazonaws.com/css/style.css"
    )

    # Test deleting files
    os.remove(mock_js_file_two)
    storage.files = storage.get_files()
    storage.sync()
    storage.files = storage.get_files()
    assert list(storage.files.keys()) == ["css/style.css", "js/index.js"]
