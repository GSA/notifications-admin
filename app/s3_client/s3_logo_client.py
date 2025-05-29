import os
import uuid

from boto3 import Session
from flask import current_app

from app.s3_client import get_s3_object
from notifications_utils.s3 import s3upload as utils_s3upload

TEMP_TAG = "temp-{user_id}_"
EMAIL_LOGO_LOCATION_STRUCTURE = "{temp}{unique_id}-{filename}"


def get_logo_location(filename=None):
    return (
        bucket_creds("bucket"),
        filename,
        bucket_creds("region"),
    )


def bucket_creds(key):
    return current_app.config["LOGO_UPLOAD_BUCKET"][key]


def delete_s3_object(filename):
    get_s3_object(*get_logo_location(filename)).delete()


def persist_logo(old_name, new_name):
    if old_name == new_name:
        return
    bucket_name, filename, region = get_logo_location(new_name)
    get_s3_object(bucket_name, filename, region).copy_from(
        CopySource="{}/{}".format(bucket_name, old_name)
    )
    delete_s3_object(old_name)


def get_s3_objects_filter_by_prefix(prefix):
    bucket_name = bucket_creds("bucket")
    session = Session(
        region_name=bucket_creds("region"),
    )
    s3 = session.resource("s3")
    return s3.Bucket(bucket_name).objects.filter(Prefix=prefix)


def get_temp_truncated_filename(filename, user_id):
    start = len(TEMP_TAG.format(user_id=user_id))
    return filename[start:]


def upload_email_logo(filename, filedata, user_id):
    upload_file_name = EMAIL_LOGO_LOCATION_STRUCTURE.format(
        temp=TEMP_TAG.format(user_id=user_id),
        unique_id=str(uuid.uuid4()),
        filename=filename,
    )
    bucket_name = bucket_creds("bucket")
    utils_s3upload(
        filedata=filedata,
        region=bucket_creds("region"),
        bucket_name=bucket_name,
        file_location=upload_file_name,
        content_type="image/png",
    )

    return upload_file_name


def permanent_email_logo_name(filename, user_id):
    if filename.startswith(TEMP_TAG.format(user_id=user_id)):
        return get_temp_truncated_filename(filename=filename, user_id=user_id)
    else:
        return filename


def delete_email_temp_files_created_by(user_id):
    for obj in get_s3_objects_filter_by_prefix(TEMP_TAG.format(user_id=user_id)):
        delete_s3_object(obj.key)


def delete_email_temp_file(filename):
    if not filename.startswith(TEMP_TAG[:5]):
        raise ValueError("Not a temp file: {}".format(filename))

    delete_s3_object(filename)
