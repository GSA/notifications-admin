import uuid

from boto3 import Session
from flask import current_app
from notifications_utils.s3 import s3upload as utils_s3upload

from app.s3_client import get_s3_object

TEMP_TAG = 'temp-{user_id}_'
EMAIL_LOGO_LOCATION_STRUCTURE = '{temp}{unique_id}-{filename}'
LETTER_PREFIX = 'letters/static/images/letter-template/'
LETTER_TEMP_TAG = LETTER_PREFIX + TEMP_TAG
LETTER_TEMP_LOGO_LOCATION = 'letters/static/images/letter-template/temp-{user_id}_{unique_id}-{filename}'


def get_logo_location(filename=None):
    return (
        current_app.config['LOGO_UPLOAD_BUCKET_NAME'],
        filename,
        current_app.config['LOGO_UPLOAD_ACCESS_KEY'],
        current_app.config['LOGO_UPLOAD_SECRET_KEY'],
        current_app.config['LOGO_UPLOAD_REGION'],
    )


def delete_s3_object(filename):
    get_s3_object(*get_logo_location(filename)).delete()


def persist_logo(old_name, new_name):
    if old_name == new_name:
        return
    bucket_name, filename, access_key, secret_key, region = get_logo_location(new_name)
    get_s3_object(bucket_name, filename, access_key, secret_key, region).copy_from(
        CopySource='{}/{}'.format(bucket_name, old_name))
    delete_s3_object(old_name)


def get_s3_objects_filter_by_prefix(prefix):
    bucket_name = current_app.config['LOGO_UPLOAD_BUCKET_NAME']
    session = Session(aws_access_key_id=current_app.config['LOGO_UPLOAD_ACCESS_KEY'],
                      aws_secret_access_key=current_app.config['LOGO_UPLOAD_SECRET_KEY'],
                      region_name=current_app.config['LOGO_UPLOAD_REGION'])
    s3 = session.resource('s3')
    return s3.Bucket(bucket_name).objects.filter(Prefix=prefix)


def get_temp_truncated_filename(filename, user_id):
    return filename[len(TEMP_TAG.format(user_id=user_id)):]


def get_letter_filename_with_no_path_or_extension(filename):
    return filename[len(LETTER_PREFIX):-4]


def upload_email_logo(filename, filedata, user_id):
    upload_file_name = EMAIL_LOGO_LOCATION_STRUCTURE.format(
        temp=TEMP_TAG.format(user_id=user_id),
        unique_id=str(uuid.uuid4()),
        filename=filename
    )
    bucket_name = current_app.config['LOGO_UPLOAD_BUCKET_NAME']
    utils_s3upload(
        filedata=filedata,
        region=current_app.config['LOGO_UPLOAD_REGION'],
        bucket_name=bucket_name,
        file_location=upload_file_name,
        content_type='image/png',
        access_key=current_app.config['LOGO_UPLOAD_ACCESS_KEY'],
        secret_key=current_app.config['LOGO_UPLOAD_SECRET_KEY'],
    )

    return upload_file_name


def upload_letter_temp_logo(filename, filedata, user_id):
    upload_filename = LETTER_TEMP_LOGO_LOCATION.format(
        user_id=user_id,
        unique_id=str(uuid.uuid4()),
        filename=filename
    )
    bucket_name = current_app.config['LOGO_UPLOAD_BUCKET_NAME']
    utils_s3upload(
        filedata=filedata,
        region=current_app.config['LOGO_UPLOAD_REGION'],
        bucket_name=bucket_name,
        file_location=upload_filename,
        content_type='image/svg+xml',
        access_key=current_app.config['LOGO_UPLOAD_ACCESS_KEY'],
        secret_key=current_app.config['LOGO_UPLOAD_SECRET_KEY'],
    )

    return upload_filename


def permanent_email_logo_name(filename, user_id):
    if filename.startswith(TEMP_TAG.format(user_id=user_id)):
        return get_temp_truncated_filename(filename=filename, user_id=user_id)
    else:
        return filename


def permanent_letter_logo_name(filename, extension):
    return LETTER_PREFIX + filename + '.' + extension


def letter_filename_for_db(filename, user_id):
    filename = get_letter_filename_with_no_path_or_extension(filename)

    if filename.startswith(TEMP_TAG.format(user_id=user_id)):
        filename = get_temp_truncated_filename(filename=filename, user_id=user_id)

    return filename


def delete_email_temp_files_created_by(user_id):
    for obj in get_s3_objects_filter_by_prefix(TEMP_TAG.format(user_id=user_id)):
        delete_s3_object(obj.key)


def delete_letter_temp_files_created_by(user_id):
    for obj in get_s3_objects_filter_by_prefix(LETTER_TEMP_TAG.format(user_id=user_id)):
        delete_s3_object(obj.key)


def delete_email_temp_file(filename):
    if not filename.startswith(TEMP_TAG[:5]):
        raise ValueError('Not a temp file: {}'.format(filename))

    delete_s3_object(filename)


def delete_letter_temp_file(filename):
    if not filename.startswith(LETTER_TEMP_TAG[:43]):
        raise ValueError('Not a temp file: {}'.format(filename))

    delete_s3_object(filename)
