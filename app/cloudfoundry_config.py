import json
import os


def find_by_service_name(services, service_name):
    for i in range(len(services)):
        if services[i]['name'] == service_name:
            return services[i]
    return None


def extract_cloudfoundry_config():
    vcap_services = json.loads(os.environ['VCAP_SERVICES'])

    # Redis config
    os.environ['REDIS_URL'] = vcap_services['aws-elasticache-redis'][0]['credentials']['uri'].replace('redis', 'rediss')

    # CSV Upload Bucket Name
    bucket_service = find_by_service_name(
        vcap_services['s3'], f"notifications-api-csv-upload-bucket-{os.environ['DEPLOY_ENV']}")
    if bucket_service:
        os.environ['CSV_UPLOAD_BUCKET_NAME'] = bucket_service['credentials']['bucket']
        os.environ['CSV_UPLOAD_ACCESS_KEY'] = bucket_service['credentials']['access_key_id']
        os.environ['CSV_UPLOAD_SECRET_KEY'] = bucket_service['credentials']['secret_access_key']

    # Contact List Bucket Name
    bucket_service = find_by_service_name(
        vcap_services['s3'], f"notifications-api-contact-list-bucket-{os.environ['DEPLOY_ENV']}")
    if bucket_service:
        os.environ['CONTACT_LIST_BUCKET_NAME'] = bucket_service['credentials']['bucket']
        os.environ['CONTACT_LIST_ACCESS_KEY'] = bucket_service['credentials']['access_key_id']
        os.environ['CONTACT_LIST_SECRET_KEY'] = bucket_service['credentials']['secret_access_key']

    # Logo Upload Bucket Name
    bucket_service = find_by_service_name(
        vcap_services['s3'], f"notifications-admin-logo-upload-bucket-{os.environ['DEPLOY_ENV']}")
    if bucket_service:
        os.environ['LOGO_UPLOAD_BUCKET_NAME'] = bucket_service['credentials']['bucket']
        os.environ['LOGO_UPLOAD_ACCESS_KEY'] = bucket_service['credentials']['access_key_id']
        os.environ['LOGO_UPLOAD_SECRET_KEY'] = bucket_service['credentials']['secret_access_key']
