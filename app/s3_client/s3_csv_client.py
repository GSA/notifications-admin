import uuid

from flask import current_app
from notifications_utils.s3 import s3upload as utils_s3upload

from app.s3_client import (
    get_s3_contents,
    get_s3_metadata,
    get_s3_object,
    set_s3_metadata,
)

FILE_LOCATION_STRUCTURE = 'service-{}-notify/{}.csv'


def get_csv_location(service_id, upload_id):
    return (
        current_app.config['CSV_UPLOAD_BUCKET']['bucket'],
        FILE_LOCATION_STRUCTURE.format(service_id, upload_id),
        current_app.config['CSV_UPLOAD_BUCKET']['access_key_id'],
        current_app.config['CSV_UPLOAD_BUCKET']['secret_access_key'],
        current_app.config['CSV_UPLOAD_BUCKET']['region'],
    )


def get_csv_upload(service_id, upload_id):
    return get_s3_object(*get_csv_location(service_id, upload_id))


def s3upload(service_id, filedata):
    upload_id = str(uuid.uuid4())
    bucket_name, file_location, access_key, secret_key, region = get_csv_location(service_id, upload_id)
    utils_s3upload(
        filedata=filedata['data'],
        region=region,
        bucket_name=bucket_name,
        file_location=file_location,
        access_key=access_key,
        secret_key=secret_key,
    )
    return upload_id


def s3download(service_id, upload_id):
    return get_s3_contents(get_csv_upload(service_id, upload_id))


def set_metadata_on_csv_upload(service_id, upload_id, **kwargs):
    return set_s3_metadata(get_csv_upload(service_id, upload_id), **kwargs)


def get_csv_metadata(service_id, upload_id):
    return get_s3_metadata(get_csv_upload(service_id, upload_id))
