import json
from os import getenv

import newrelic.agent
import pytz

from app.cloudfoundry_config import cloud_config


class Config(object):
    NOTIFY_APP_NAME = 'admin'
    NOTIFY_ENVIRONMENT = getenv('NOTIFY_ENVIRONMENT', 'development')
    API_HOST_NAME = getenv('API_HOST_NAME', 'localhost')
    ADMIN_BASE_URL = getenv('ADMIN_BASE_URL', 'http://localhost:6012')
    HEADER_COLOUR = '#81878b'  # mix(govuk-colour("dark-grey"), govuk-colour("mid-grey"))
    LOGO_CDN_DOMAIN = 'static-logos.notifications.service.gov.uk'  # TODO use our own CDN
    ASSETS_DEBUG = False
    TIMEZONE = getenv('TIMEZONE', 'America/New_York')
    PY_TIMEZONE = pytz.timezone(TIMEZONE)

    # Credentials
    ADMIN_CLIENT_SECRET = getenv('ADMIN_CLIENT_SECRET')
    ADMIN_CLIENT_USER_NAME = getenv('ADMIN_CLIENT_USERNAME')
    SECRET_KEY = getenv('SECRET_KEY')
    DANGEROUS_SALT = getenv('DANGEROUS_SALT')
    # ZENDESK_API_KEY = getenv('ZENDESK_API_KEY')
    ROUTE_SECRET_KEY_1 = getenv('ROUTE_SECRET_KEY_1', 'dev-route-secret-key-1')
    ROUTE_SECRET_KEY_2 = getenv('ROUTE_SECRET_KEY_2', 'dev-route-secret-key-2')
    BASIC_AUTH_USERNAME = getenv('BASIC_AUTH_USERNAME')
    BASIC_AUTH_PASSWORD = getenv('BASIC_AUTH_PASSWORD')

    NR_ACCOUNT_ID = getenv('NR_ACCOUNT_ID')
    NR_TRUST_KEY = getenv('NR_TRUST_KEY')
    NR_AGENT_ID = getenv('NR_AGENT_ID')
    NR_APP_ID = getenv('NR_APP_ID')
    NR_BROWSER_KEY = getenv('NR_BROWSER_KEY')
    settings = newrelic.agent.global_settings()
    NR_MONITOR_ON = settings and settings.monitor_mode

    TEMPLATE_PREVIEW_API_HOST = getenv('TEMPLATE_PREVIEW_API_HOST', 'http://localhost:9999')
    TEMPLATE_PREVIEW_API_KEY = getenv('TEMPLATE_PREVIEW_API_KEY', 'my-secret-key')

    # Logging
    NOTIFY_LOG_LEVEL = getenv('NOTIFY_LOG_LEVEL', 'INFO')

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

    REDIS_URL = cloud_config.redis_url
    REDIS_ENABLED = getenv('REDIS_ENABLED', '1') == '1'

    # TODO: reassign this
    NOTIFY_SERVICE_ID = 'd6aa2c68-a2d9-4437-ab19-3ae8eb202553'

    NOTIFY_BILLING_DETAILS = json.loads(
        getenv('NOTIFY_BILLING_DETAILS') or 'null'
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


def _s3_credentials_from_env(bucket_prefix):
    return {
        'bucket': getenv(f"{bucket_prefix}_BUCKET_NAME", f"{bucket_prefix}-test-bucket-name"),
        'access_key_id': getenv(f"{bucket_prefix}_AWS_ACCESS_KEY_ID"),
        'secret_access_key': getenv(f"{bucket_prefix}_AWS_SECRET_ACCESS_KEY"),
        'region': getenv(f"{bucket_prefix}_AWS_REGION")
    }


class Development(Config):
    BASIC_AUTH_FORCE = False
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    HTTP_PROTOCOL = 'http'
    ASSET_DOMAIN = ''
    ASSET_PATH = '/static/'
    NOTIFY_LOG_LEVEL = 'DEBUG'

    # Buckets
    CSV_UPLOAD_BUCKET = _s3_credentials_from_env('CSV')
    LOGO_UPLOAD_BUCKET = _s3_credentials_from_env('LOGO')

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


class Production(Config):
    HEADER_COLOUR = '#005EA5'  # $govuk-blue
    HTTP_PROTOCOL = 'https'
    BASIC_AUTH_FORCE = True
    ASSET_DOMAIN = ''  # TODO use a CDN
    ASSET_PATH = '/static/'  # TODO use a CDN
    DEBUG = False

    # buckets
    CSV_UPLOAD_BUCKET = cloud_config.s3_credentials(
        f"notify-api-csv-upload-bucket-{getenv('NOTIFY_ENVIRONMENT')}")
    LOGO_UPLOAD_BUCKET = cloud_config.s3_credentials(
        f"notify-admin-logo-upload-bucket-{getenv('NOTIFY_ENVIRONMENT')}")


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
    API_HOST_NAME = 'https://notify-api-staging.app.cloud.gov/'
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
