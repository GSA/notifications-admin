from functools import wraps

from flask import abort, current_app
from flask_login import current_user, login_required

from app import config
from notifications_utils.clients.redis import redis_client

user_is_logged_in = login_required


def user_has_permissions(*permissions, **permission_kwargs):
    def wrap(func):
        @wraps(func)
        def wrap_func(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            if not current_user.has_permissions(*permissions, **permission_kwargs):
                abort(403)
            return func(*args, **kwargs)

        return wrap_func

    return wrap


def user_is_gov_user(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not current_user.is_gov_user:
            abort(403)
        return f(*args, **kwargs)

    return wrapped


def user_is_platform_admin(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not current_user.platform_admin:
            abort(403)
        return f(*args, **kwargs)

    return wrapped


def is_gov_user(email_address):
    return _email_address_ends_with(
        email_address, config.Config.GOVERNMENT_EMAIL_DOMAIN_NAMES
    )  # or _email_address_ends_with(email_address, organizations_client.get_domains())


def _email_address_ends_with(email_address, known_domains):
    return any(
        email_address.lower().endswith(
            (
                "@{}".format(known),
                ".{}".format(known),
            )
        )
        for known in known_domains
    )


# def normalise_email_address_aliases(email_address):
#     local_part, domain = email_address.split('@')
#     local_part = local_part.split('+')[0].replace('.', '')

#     return f'{local_part}@{domain}'.lower()


# def distinct_email_addresses(*args):
#     return len(args) == len(set(map(normalise_email_address_aliases, args)))


def get_from_session(session_id, key):
    return redis_client.get(f"{session_id}-{key}")

def set_to_session(session_id, key, value):
    redis_client.set(f"{session_id}-{key}", value)
