from functools import wraps

from flask import abort, current_app
from flask_login import current_user, login_required

from app import config
from app.extensions import redis_client

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


def session_pop(key, altval=None):
    return_val = get_from_session(key)
    redis_client.delete(key)
    if return_val is None and altval is not None:
        return altval
    return return_val


def session_clear():
    key = current_user.current_session_id
    for k in redis_client.keys(pattern=f"{key}*"):
        if k.startswith(key):
            session_pop(k)

def check_session(key):
    compound_key = f"{current_user.current_session_id}-{key}"
    for k in redis_client.keys(pattern=f"{key}*"):
        if k is compound_key:
            return True
    return False

def get_from_session(key):
    compound_key = f"{current_user.current_session_id}-{key}"
    return redis_client.get(compound_key)


def set_to_session(key, value):
    compound_key = f"{current_user.current_session_id}-{key}"
    redis_client.set(compound_key, value)
