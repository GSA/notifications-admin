import os
import uuid

import boto3
from flask import current_app

from app.s3_client import (
    AWS_CLIENT_CONFIG,
    get_s3_contents,
    get_s3_metadata,
    get_s3_object,
    set_s3_metadata,
)
from notifications_utils.s3 import s3upload as utils_s3upload

NEW_FILE_LOCATION_STRUCTURE = "{}-service-notify/{}.csv"


def get_csv_location(service_id, upload_id):
    return (
        current_app.config["CSV_UPLOAD_BUCKET"]["bucket"],
        NEW_FILE_LOCATION_STRUCTURE.format(service_id, upload_id),
        current_app.config["CSV_UPLOAD_BUCKET"]["access_key_id"],
        current_app.config["CSV_UPLOAD_BUCKET"]["secret_access_key"],
        current_app.config["CSV_UPLOAD_BUCKET"]["region"],
    )


def get_csv_upload(service_id, upload_id):
    return get_s3_object(*get_csv_location(service_id, upload_id))


def s3upload(service_id, filedata):

    upload_id = str(uuid.uuid4())
    bucket_name, file_location, access_key, secret_key, region = get_csv_location(
        service_id, upload_id
    )
    if bucket_name == "":
        exp_bucket = current_app.config["CSV_UPLOAD_BUCKET"]["bucket"]
        exp_region = current_app.config["CSV_UPLOAD_BUCKET"]["region"]
        tier = os.getenv("NOTIFY_ENVIRONMENT")
        raise Exception(
            f"NO BUCKET NAME SHOULD BE: {exp_bucket} WITH REGION {exp_region} TIER {tier}"
        )

    utils_s3upload(
        filedata=filedata["data"],
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


def report_upload(file_location, report_content):
    bucket_name = current_app.config["CSV_UPLOAD_BUCKET"]["bucket"]
    access_key = current_app.config["CSV_UPLOAD_BUCKET"]["access_key_id"]
    secret_key = current_app.config["CSV_UPLOAD_BUCKET"]["secret_access_key"]
    region = current_app.config["CSV_UPLOAD_BUCKET"]["region"]

    utils_s3upload(
        filedata=report_content,
        region=region,
        bucket_name=bucket_name,
        file_location=file_location,
        access_key=access_key,
        secret_key=secret_key,
    )
    current_app.logger.info(f"Succcessfully uploaded report to {file_location}")


def report_download(file_location):
    current_app.logger.info(f"Downloading report from {file_location}")
    bucket_name = current_app.config["CSV_UPLOAD_BUCKET"]["bucket"]
    access_key = current_app.config["CSV_UPLOAD_BUCKET"]["access_key_id"]
    secret_key = current_app.config["CSV_UPLOAD_BUCKET"]["secret_access_key"]
    region = current_app.config["CSV_UPLOAD_BUCKET"]["region"]

    return get_s3_contents(
        get_s3_object(bucket_name, file_location, access_key, secret_key, region)
    )


def delete_report(file_location):
    current_app.logger.info(f"Deleting report from {file_location}")
    bucket_name = current_app.config["CSV_UPLOAD_BUCKET"]["bucket"]
    access_key = current_app.config["CSV_UPLOAD_BUCKET"]["access_key_id"]
    secret_key = current_app.config["CSV_UPLOAD_BUCKET"]["secret_access_key"]
    region = current_app.config["CSV_UPLOAD_BUCKET"]["region"]

    obj = get_s3_object(bucket_name, file_location, access_key, secret_key, region)
    if obj is None:
        return None
    return obj.delete()


def get_downloadable_reports(user_id, service_id):
    prefix = f"reports/{service_id}/{user_id}/"
    bucket_name = current_app.config["CSV_UPLOAD_BUCKET"]["bucket"]
    access_key = current_app.config["CSV_UPLOAD_BUCKET"]["access_key_id"]
    secret_key = current_app.config["CSV_UPLOAD_BUCKET"]["secret_access_key"]
    region = current_app.config["CSV_UPLOAD_BUCKET"]["region"]

    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    s3 = session.client(
        "s3",
        config=AWS_CLIENT_CONFIG,
    )

    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    object_keys = []
    if "Contents" in response:
        for obj in response["Contents"]:
            object_keys.append(obj["Key"])
    return object_keys
