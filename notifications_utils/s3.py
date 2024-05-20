import os
import urllib

import botocore
from boto3 import Session
from botocore.config import Config
from flask import current_app

AWS_CLIENT_CONFIG = Config(
    # This config is required to enable S3 to connect to FIPS-enabled
    # endpoints.  See https://aws.amazon.com/compliance/fips/ for more
    # information.
    s3={
        "addressing_style": "virtual",
    },
    use_fips_endpoint=True,
)

default_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
default_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
default_region = os.environ.get("AWS_REGION")


def s3upload(
    filedata,
    region,
    bucket_name,
    file_location,
    content_type="binary/octet-stream",
    tags=None,
    metadata=None,
    access_key=default_access_key_id,
    secret_key=default_secret_access_key,
):
    session = Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    _s3 = session.resource("s3", config=AWS_CLIENT_CONFIG)

    key = _s3.Object(bucket_name, file_location)

    put_args = {
        "Body": filedata,
        "ServerSideEncryption": "AES256",
        "ContentType": content_type,
    }

    if tags:
        tags = urllib.parse.urlencode(tags)
        put_args["Tagging"] = tags

    if metadata:
        metadata = put_args["Metadata"] = metadata

    try:
        key.put(**put_args)
    except botocore.exceptions.ClientError as e:
        current_app.logger.error(
            "Unable to upload file to S3 bucket {}".format(bucket_name)
        )
        raise e


class S3ObjectNotFound(botocore.exceptions.ClientError):
    pass


def s3download(
    bucket_name,
    filename,
    region=default_region,
    access_key=default_access_key_id,
    secret_key=default_secret_access_key,
):
    try:
        session = Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        s3 = session.resource("s3", config=AWS_CLIENT_CONFIG)
        key = s3.Object(bucket_name, filename)
        return key.get()["Body"]
    except botocore.exceptions.ClientError as error:
        raise S3ObjectNotFound(error.response, error.operation_name)
