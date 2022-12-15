import json
import os

import pytz

from app.cloudfoundry_config import cloud_config


class Config(object):
    NOTIFY_APP_NAME = 'admin'
    NOTIFY_ENVIRONMENT = os.environ.get('NOTIFY_ENVIRONMENT', 'development')
    API_HOST_NAME = os.environ.get('API_HOST_NAME', 'localhost')
    ADMIN_BASE_URL = os.environ.get('ADMIN_BASE_URL', 'http://localhost:6012')
    HEADER_COLOUR = '#81878b'  # mix(govuk-colour("dark-grey"), govuk-colour("mid-grey"))
    LOGO_CDN_DOMAIN = 'static-logos.notifications.service.gov.uk'  # TODO use our own CDN
    ASSETS_DEBUG = False
    TIMEZONE = os.environ.get('TIMEZONE', 'America/New_York')
    PY_TIMEZONE = pytz.timezone(TIMEZONE)

    # Credentials
    ADMIN_CLIENT_SECRET = os.environ.get('ADMIN_CLIENT_SECRET')
    ADMIN_CLIENT_USER_NAME = os.environ.get('ADMIN_CLIENT_USERNAME')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DANGEROUS_SALT = os.environ.get('DANGEROUS_SALT')
    # ZENDESK_API_KEY = os.environ.get('ZENDESK_API_KEY')
    ROUTE_SECRET_KEY_1 = os.environ.get('ROUTE_SECRET_KEY_1', 'dev-route-secret-key-1')
    ROUTE_SECRET_KEY_2 = os.environ.get('ROUTE_SECRET_KEY_2', 'dev-route-secret-key-2')
    BASIC_AUTH_USERNAME = os.environ.get('BASIC_AUTH_USERNAME')
    BASIC_AUTH_PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD')

    TEMPLATE_PREVIEW_API_HOST = os.environ.get('TEMPLATE_PREVIEW_API_HOST', 'http://localhost:9999')
    TEMPLATE_PREVIEW_API_KEY = os.environ.get('TEMPLATE_PREVIEW_API_KEY', 'my-secret-key')

    # Logging
    NOTIFY_LOG_LEVEL = os.environ.get('NOTIFY_LOG_LEVEL', 'INFO')

    DEFAULT_SERVICE_LIMIT = 50

    EMAIL_EXPIRY_SECONDS = 3600  # 1 hour
    INVITATION_EXPIRY_SECONDS = 3600 * 24 * 2  # 2 days - also set on api
    EMAIL_2FA_EXPIRY_SECONDS = 1800  # 30 Minutes
    PERMANENT_SESSION_LIFETIME = 20 * 60 * 60  # 20 hours
    SEND_FILE_MAX_AGE_DEFAULT = 365 * 24 * 60 * 60  # 1 year
    REPLY_TO_EMAIL_ADDRESS_VALIDATION_TIMEOUT = 45
    ACTIVITY_STATS_LIMIT_DAYS = 7
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_NAME = 'notify_admin_session'
    SESSION_COOKIE_SECURE = True
    # don't send back the cookie if it hasn't been modified by the request. this means that the expiry time won't be
    # updated unless the session is changed - but it's generally refreshed by `save_service_or_org_after_request`
    # every time anyway, except for specific endpoints (png/pdfs generally) where we've disabled that handler.
    SESSION_REFRESH_EACH_REQUEST = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    CHECK_PROXY_HEADER = False

    AWS_REGION = os.environ.get('AWS_REGION')

    REDIS_URL = cloud_config.redis_url
    REDIS_ENABLED = os.environ.get('REDIS_ENABLED', '1') == '1'

    # TODO: reassign this
    NOTIFY_SERVICE_ID = 'd6aa2c68-a2d9-4437-ab19-3ae8eb202553'

    NOTIFY_BILLING_DETAILS = json.loads(
        os.environ.get('NOTIFY_BILLING_DETAILS') or 'null'
    ) or {
        'account_number': '98765432',
        'sort_code': '01-23-45',
        'IBAN': 'GB33BUKB20201555555555',
        'swift': 'ABCDEF12',
        'notify_billing_email_addresses': [
            'generic@digital.cabinet-office.gov.uk',
            'first.last@digital.cabinet-office.gov.uk',
        ]
    }


def _default_s3_credentials(bucket_name):
    return {
        'bucket': bucket_name,
        'access_key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
        'secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
        'region': os.environ.get('AWS_REGION')
    }


class Development(Config):
    BASIC_AUTH_FORCE = False
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    HTTP_PROTOCOL = 'http'
    ASSET_DOMAIN = ''
    ASSET_PATH = '/static/'

    # Buckets
    CSV_UPLOAD_BUCKET = _default_s3_credentials('local-notifications-csv-upload')
    CONTACT_LIST_BUCKET = _default_s3_credentials('local-contact-list')
    LOGO_UPLOAD_BUCKET = _default_s3_credentials('local-public-logos-tools')

    # credential overrides
    DANGEROUS_SALT = 'development-notify-salt'
    SECRET_KEY = 'dev-notify-secret-key'  # nosec B105 - only used in development
    # ADMIN_CLIENT_USER_NAME is called ADMIN_CLIENT_ID in api repo, they should match
    ADMIN_CLIENT_USER_NAME = 'notify-admin'
    ADMIN_CLIENT_SECRET = 'dev-notify-secret-key'  # nosec B105 - only used in development


class Test(Development):
    TESTING = True
    WTF_CSRF_ENABLED = False
    ASSET_DOMAIN = 'static.example.com'
    ASSET_PATH = 'https://static.example.com/'

    API_HOST_NAME = 'http://you-forgot-to-mock-an-api-call-to'
    REDIS_URL = 'redis://you-forgot-to-mock-a-redis-call-to'
    LOGO_CDN_DOMAIN = 'static-logos.test.com'

    # Buckets
    CSV_UPLOAD_BUCKET = _default_s3_credentials('test-csv-upload')
    CONTACT_LIST_BUCKET = _default_s3_credentials('test-contact-list')
    LOGO_UPLOAD_BUCKET = _default_s3_credentials('test-logo-upload')


class Production(Config):
    HEADER_COLOUR = '#005EA5'  # $govuk-blue
    HTTP_PROTOCOL = 'https'
    BASIC_AUTH_FORCE = True
    ASSET_DOMAIN = ''  # TODO use a CDN
    ASSET_PATH = '/static/'  # TODO use a CDN
    DEBUG = False

    # buckets
    CSV_UPLOAD_BUCKET = cloud_config.s3_credentials(
        f"notify-api-csv-upload-bucket-{os.environ['NOTIFY_ENVIRONMENT']}")
    CONTACT_LIST_BUCKET = cloud_config.s3_credentials(
        f"notify-api-contact-list-bucket-{os.environ['NOTIFY_ENVIRONMENT']}")
    LOGO_UPLOAD_BUCKET = cloud_config.s3_credentials(
        f"notify-admin-logo-upload-bucket-{os.environ['NOTIFY_ENVIRONMENT']}")


class Staging(Production):
    BASIC_AUTH_FORCE = True
    HEADER_COLOUR = '#00ff00'  # $green


class Demo(Staging):
    HEADER_COLOUR = '#6F72AF'  # $mauve


class Sandbox(Staging):
    HEADER_COLOUR = '#ff0000'  # $red


class Scanning(Production):
    BASIC_AUTH_FORCE = False
    HTTP_PROTOCOL = 'http'
    API_HOST_NAME = 'https://notify-api-demo.app.cloud.gov/'
    SECRET_KEY = 'dev-notify-secret-key'  # nosec B105 - only used in development
    ADMIN_CLIENT_USER_NAME = 'notify-admin'
    ADMIN_CLIENT_SECRET = 'dev-notify-secret-key'  # nosec B105 - only used in development


configs = {
    'development': Development,
    'test': Test,
    'scanning': Scanning,
    'staging': Staging,
    'demo': Demo,
    'sandbox': Sandbox,
    'production': Production
}
