from setuptools import find_packages, setup

from asgi_s3.__version__ import __version__


def get_long_description():
    return open("README.md", "r", encoding="utf8").read()


setup(
    name="asgi-s3",
    version=__version__,
    packages=find_packages(),
    license="MIT",
    url="https://github.com/erm/asgi-s3",
    description="ASGI S3 storage",
    long_description=get_long_description(),
    install_requires=["boto3", "click", 'contextvars;python_version<"3.7"'],
    entry_points={"console_scripts": ["s3 = asgi_s3.__main__:main"]},
    long_description_content_type="text/markdown",
    author="Jordan Eremieff",
    author_email="jordan@eremieff.com",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
)
