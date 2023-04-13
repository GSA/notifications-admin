import botocore
from flask import current_app

from app.s3_client.s3_logo_client import get_s3_object


def get_mou():
    bucket = current_app.config['MOU_BUCKET_NAME']
    filename = 'agreement.pdf'
    attachment_filename = 'U.S. Notify data sharing and financial agreement.pdf'.format(
    )
    try:
        key = get_s3_object(bucket, filename)
        return {
            'path_or_file': key.get()['Body'],
            'download_name': attachment_filename,
            'as_attachment': True,
        }
    except botocore.exceptions.ClientError as exception:
        current_app.logger.error("Unable to download s3 file {}/{}".format(
            bucket, filename
        ))
        raise exception
