import botocore
from boto3 import Session
from botocore.config import Config
from flask import current_app

AWS_CLIENT_CONFIG = Config(
    # This config is required to enable S3 to connect to FIPS-enabled
    # endpoints.  See https://aws.amazon.com/compliance/fips/ for more
    # information.
    s3={
        'addressing_style': 'virtual',
    },
    use_fips_endpoint=True
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
        config=AWS_CLIENT_CONFIG
    )
    s3 = session.resource('s3')
    obj = s3.Object(bucket_name, filename)
    return obj


def get_s3_metadata(obj):
    try:
        return obj.get()['Metadata']
    except botocore.exceptions.ClientError as client_error:
        current_app.logger.error(f"Unable to download s3 file {obj.bucket_name}/{obj.key}")
        raise client_error


def set_s3_metadata(obj, **kwargs):
    copy_from_object_result = obj.copy_from(
        CopySource=f"{obj.bucket_name}/{obj.key}",
        ServerSideEncryption='AES256',
        Metadata={
            key: str(value) for key, value in kwargs.items()
        },
        MetadataDirective='REPLACE',
    )
    return copy_from_object_result


def get_s3_contents(obj):
    contents = ''
    try:
        contents = obj.get()['Body'].read().decode('utf-8')
    except botocore.exceptions.ClientError as client_error:
        current_app.logger.error(f"Unable to download s3 file {obj.bucket_name}/{obj.key}")
        raise client_error
    return contents
