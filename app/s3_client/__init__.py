import os

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


def get_s3_object(
    bucket_name,
    filename,
    access_key,
    secret_key,
    region,
):
    # To inspect contents: obj.get()['Body'].read().decode('utf-8')
    session = Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    s3 = session.resource(
        "s3", endpoint_url="https://s3-fips.us-gov-west-1.amazonaws.com"
    )
    obj = s3.Object(bucket_name, filename)
    # This 'proves' that use of moto in the relevant tests in test_send.py
    # mocks everything related to S3.  What you will see in the logs is:
    # Exception: CREATED AT <MagicMock name='resource().Bucket().creation_date' id='4665562448'>
    #
    # raise Exception(f"CREATED AT {_s3.Bucket(bucket_name).creation_date}")
    if os.getenv("NOTIFY_ENVIRONMENT") == "test":
        teststr = str(s3.Bucket(bucket_name).creation_date).lower()
        if "magicmock" not in teststr:
            raise Exception(
                "Test is not mocked, use @mock_aws or the relevant mocker.patch to avoid accessing S3"
            )
    return obj


def get_s3_metadata(obj):
    try:
        return obj.get()["Metadata"]
    except botocore.exceptions.ClientError as client_error:
        current_app.logger.error(
            f"Unable to download s3 file {obj.bucket_name}/{obj.key}"
        )
        raise client_error


def set_s3_metadata(obj, **kwargs):
    copy_from_object_result = obj.copy_from(
        CopySource=f"{obj.bucket_name}/{obj.key}",
        ServerSideEncryption="AES256",
        Metadata={key: str(value) for key, value in kwargs.items()},
        MetadataDirective="REPLACE",
    )
    return copy_from_object_result


def get_s3_contents(obj):
    contents = ""
    try:
        contents = obj.get()["Body"].read().decode("utf-8")
    except botocore.exceptions.ClientError as client_error:
        current_app.logger.error(
            f"Unable to download s3 file {obj.bucket_name}/{obj.key}"
        )
        raise client_error
    return contents
