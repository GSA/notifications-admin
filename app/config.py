import json
import os

if os.environ.get('VCAP_SERVICES'):
    # on cloudfoundry, config is a json blob in VCAP_SERVICES - unpack it, and populate
    # standard environment variables from it
    from app.cloudfoundry_config import extract_cloudfoundry_config
    extract_cloudfoundry_config()


class Config(object):
    NOTIFY_APP_NAME = 'admin'
    NOTIFY_ENVIRONMENT = os.environ.get('NOTIFY_ENVIRONMENT', 'development')
    API_HOST_NAME = os.environ.get('API_HOST_NAME', 'localhost')
    ADMIN_BASE_URL = os.environ.get('ADMIN_BASE_URL', 'http://localhost:6012')
    HEADER_COLOUR = '#81878b'  # mix(govuk-colour("dark-grey"), govuk-colour("mid-grey"))
    LOGO_CDN_DOMAIN = 'static-logos.notifications.service.gov.uk'  # TODO use our own CDN
    ASSETS_DEBUG = False

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
    ANTIVIRUS_API_HOST = os.environ.get('ANTIVIRUS_API_HOST', 'http://localhost:6016')
    ANTIVIRUS_API_KEY = os.environ.get('ANTIVIRUS_API_KEY', 'test-key')

    # Logging
    NOTIFY_LOG_LEVEL = os.environ.get('NOTIFY_LOG_LEVEL', 'INFO')
    NOTIFY_LOG_PATH = os.environ.get('NOTIFY_LOG_PATH', 'application.log')

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
    ANTIVIRUS_ENABLED = os.environ.get('ANTIVIRUS_ENABLED') == '1'

    AWS_REGION = os.environ.get('AWS_REGION')

    REDIS_URL = os.environ.get('REDIS_URL')
    REDIS_ENABLED = os.environ.get('REDIS_ENABLED', '1') == '1'

    # as defined in api db migration 0331_add_broadcast_org.py
    BROADCAST_ORGANISATION_ID = '38e4bf69-93b0-445d-acee-53ea53fe02df'

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


class Development(Config):
    BASIC_AUTH_FORCE = False
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    HTTP_PROTOCOL = 'http'
    ASSET_DOMAIN = ''
    ASSET_PATH = '/static/'

    # Buckets
    CSV_UPLOAD_BUCKET_NAME = 'local-notifications-csv-upload'  # created in gsa sandbox
    CSV_UPLOAD_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
    CSV_UPLOAD_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    CSV_UPLOAD_REGION = os.environ.get('AWS_REGION')
    CONTACT_LIST_UPLOAD_BUCKET_NAME = 'local-contact-list'  # created in gsa sandbox
    CONTACT_LIST_UPLOAD_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
    CONTACT_LIST_UPLOAD_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    CONTACT_LIST_UPLOAD_REGION = os.environ.get('AWS_REGION')
    LOGO_UPLOAD_BUCKET_NAME = 'local-public-logos-tools'  # created in gsa sandbox
    LOGO_UPLOAD_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
    LOGO_UPLOAD_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    LOGO_UPLOAD_REGION = os.environ.get('AWS_REGION')
    # MOU_BUCKET_NAME = 'local-notify-tools-mou'  # not created in gsa sandbox
    # TRANSIENT_UPLOADED_LETTERS = 'development-transient-uploaded-letters'  # not created in gsa sandbox
    # PRECOMPILED_ORIGINALS_BACKUP_LETTERS =
    # 'development-letters-precompiled-originals-backup'  # not created in sandbox

    # credential overrides
    DANGEROUS_SALT = 'dev-notify-salt'
    SECRET_KEY = 'dev-notify-secret-key'  # nosec B105 - only used in development
    # ADMIN_CLIENT_USER_NAME is called ADMIN_CLIENT_ID in api repo, they should match
    ADMIN_CLIENT_USER_NAME = 'notify-admin'
    ADMIN_CLIENT_SECRET = 'dev-notify-secret-key'  # nosec B105 - only used in development


class Test(Development):
    TESTING = True
    WTF_CSRF_ENABLED = False
    ASSET_DOMAIN = 'static.example.com'
    ASSET_PATH = 'https://static.example.com/'

    # none of these buckets actually exist
    CSV_UPLOAD_BUCKET_NAME = 'test-notifications-csv-upload'
    CONTACT_LIST_UPLOAD_BUCKET_NAME = 'test-contact-list'
    LOGO_UPLOAD_BUCKET_NAME = 'public-logos-test'
    # MOU_BUCKET_NAME = 'test-mou'
    # TRANSIENT_UPLOADED_LETTERS = 'test-transient-uploaded-letters'
    # PRECOMPILED_ORIGINALS_BACKUP_LETTERS = 'test-letters-precompiled-originals-backup'

    API_HOST_NAME = 'http://you-forgot-to-mock-an-api-call-to'
    REDIS_URL = 'redis://you-forgot-to-mock-a-redis-call-to'
    ANTIVIRUS_API_HOST = 'https://test-antivirus'
    ANTIVIRUS_API_KEY = 'test-antivirus-secret'
    ANTIVIRUS_ENABLED = True
    LOGO_CDN_DOMAIN = 'static-logos.test.com'


class Production(Config):
    HEADER_COLOUR = '#005EA5'  # $govuk-blue
    HTTP_PROTOCOL = 'https'
    BASIC_AUTH_FORCE = True
    ASSET_DOMAIN = ''  # TODO use a CDN
    ASSET_PATH = '/static/'  # TODO use a CDN
    DEBUG = False

    # buckets
    CSV_UPLOAD_BUCKET_NAME = os.environ.get('CSV_UPLOAD_BUCKET_NAME')
    CSV_UPLOAD_ACCESS_KEY = os.environ.get('CSV_UPLOAD_ACCESS_KEY')
    CSV_UPLOAD_SECRET_KEY = os.environ.get('CSV_UPLOAD_SECRET_KEY')
    CSV_UPLOAD_REGION = os.environ.get('CSV_UPLOAD_REGION')
    CONTACT_LIST_UPLOAD_BUCKET_NAME = os.environ.get('CONTACT_LIST_BUCKET_NAME')
    CONTACT_LIST_UPLOAD_ACCESS_KEY = os.environ.get('CONTACT_LIST_ACCESS_KEY')
    CONTACT_LIST_UPLOAD_SECRET_KEY = os.environ.get('CONTACT_LIST_SECRET_KEY')
    CONTACT_LIST_UPLOAD_REGION = os.environ.get('CONTACT_LIST_REGION')
    LOGO_UPLOAD_BUCKET_NAME = os.environ.get('LOGO_UPLOAD_BUCKET_NAME')
    LOGO_UPLOAD_ACCESS_KEY = os.environ.get('LOGO_UPLOAD_ACCESS_KEY')
    LOGO_UPLOAD_SECRET_KEY = os.environ.get('LOGO_UPLOAD_SECRET_KEY')
    LOGO_UPLOAD_REGION = os.environ.get('LOGO_UPLOAD_REGION')
    # MOU_BUCKET_NAME = os.environ.get('MOU_UPLOAD_BUCKET_NAME')
    # TRANSIENT_UPLOADED_LETTERS = 'prototype-transient-uploaded-letters'  # not created in gsa sandbox
    # PRECOMPILED_ORIGINALS_BACKUP_LETTERS = 'prototype-letters-precompiled-originals-backup'  # not in sandbox


class Staging(Production):
    BASIC_AUTH_FORCE = True
    HEADER_COLOUR = '#6F72AF'  # $mauve


class Scanning(Production):
    BASIC_AUTH_FORCE = False
    HTTP_PROTOCOL = 'http'
    API_HOST_NAME = 'https://notifications-api.app.cloud.gov/'
    SECRET_KEY = 'dev-notify-secret-key'  # nosec B105 - only used in development
    ADMIN_CLIENT_USER_NAME = 'notify-admin'
    ADMIN_CLIENT_SECRET = 'dev-notify-secret-key'  # nosec B105 - only used in development


configs = {
    'development': Development,
    'test': Test,
    'scanning': Scanning,
    'staging': Staging,
    'production': Production
}
