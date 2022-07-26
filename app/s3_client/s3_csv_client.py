import uuid

import botocore
from flask import current_app
from notifications_utils.s3 import s3upload as utils_s3upload

from app.s3_client.s3_logo_client import get_s3_object

FILE_LOCATION_STRUCTURE = 'service-{}-notify/{}.csv'


def get_csv_location(service_id, upload_id, bucket=None):
    return (
        bucket or current_app.config['CSV_UPLOAD_BUCKET_NAME'],
        FILE_LOCATION_STRUCTURE.format(service_id, upload_id),
    )


def get_csv_upload(service_id, upload_id, bucket=None):
    s3_object = get_s3_object(*get_csv_location(service_id, upload_id, bucket))
    return s3_object


def s3upload(service_id, filedata, region, bucket=None):
    upload_id = str(uuid.uuid4())
    bucket_name, file_location = get_csv_location(service_id, upload_id, bucket)
    utils_s3upload(
        filedata=filedata['data'],
        region=region,
        bucket_name=bucket_name,
        file_location=file_location,
    )
    return upload_id


def s3download(service_id, upload_id, bucket=None):
    contents = ''
    try:
        key = get_csv_upload(service_id, upload_id, bucket)
        contents = key.get()['Body'].read().decode('utf-8')
    except botocore.exceptions.ClientError as e:
        current_app.logger.error("Unable to download s3 file {}".format(
            FILE_LOCATION_STRUCTURE.format(service_id, upload_id)))
        raise e
    return contents


def set_metadata_on_csv_upload(service_id, upload_id, bucket=None, **kwargs):
    current_app.logger.info('set_metadata_on_csv_upload, service_id: {} upload_id: {} bucket: {}'.format(service_id, upload_id, bucket))
    current_app.logger.info('csv location to copy from is: {}/{}'.format(*get_csv_location(service_id, upload_id, bucket=bucket)))
    copy_from_object_result = get_csv_upload(
        service_id, upload_id, bucket=bucket
    ).copy_from(
        CopySource='{}/{}'.format(*get_csv_location(service_id, upload_id, bucket=bucket)),
        ServerSideEncryption='AES256',
        Metadata={
            key: str(value) for key, value in kwargs.items()
        },
        MetadataDirective='REPLACE',
    )
    return copy_from_object_result


def get_csv_metadata(service_id, upload_id, bucket=None):
    try:
        key = get_csv_upload(service_id, upload_id, bucket)
        return key.get()['Metadata']
    except botocore.exceptions.ClientError as e:
        current_app.logger.error("Unable to download s3 file {}".format(
            FILE_LOCATION_STRUCTURE.format(service_id, upload_id)))
        raise e
