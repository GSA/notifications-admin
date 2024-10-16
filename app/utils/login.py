import json
import os
from functools import wraps

import jwt
import requests
from flask import current_app, redirect, request, session, url_for

from app.models.user import User
from app.utils.time import is_less_than_days_ago


def redirect_to_sign_in(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_details" not in session:
            return redirect(url_for("main.sign_in"))
        else:
            return f(*args, **kwargs)

    return wrapped


def log_in_user(user_id):
    try:
        user = User.from_id(user_id)
        # the user will have a new current_session_id set by the API - store it in the cookie for future requests
        session["current_session_id"] = user.current_session_id
        # Check if coming from new password page
        if "password" in session.get("user_details", {}):
            user.update_password(session["user_details"]["password"])
        user.activate()
        user.login()
    finally:
        # get rid of anything in the session that we don't expect to have been set during register/sign in flow
        session.pop("user_details", None)
        session.pop("file_uploads", None)

    return redirect_when_logged_in(platform_admin=user.platform_admin)


def redirect_when_logged_in(platform_admin):
    next_url = request.args.get("next")
    if next_url and is_safe_redirect_url(next_url):
        return redirect(next_url)

    return redirect(url_for("main.show_accounts_or_dashboard"))


def email_needs_revalidating(user):
    return not is_less_than_days_ago(user.email_access_validated_at, 90)


# see https://stackoverflow.com/questions/60532973/how-do-i-get-a-is-safe-url-function-to-use-with-flask-and-how-does-it-work  # noqa
def is_safe_redirect_url(target):
    from urllib.parse import urljoin, urlparse

    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return (
        redirect_url.scheme in ("http", "https")
        and host_url.netloc == redirect_url.netloc
    )


def get_id_token(json_data):
    """Decode and return the id_token."""
    client_id = os.getenv("LOGIN_DOT_GOV_CLIENT_ID")
    certs_url = os.getenv("LOGIN_DOT_GOV_CERTS_URL")

    try:
        encoded_id_token = json_data["id_token"]
    except KeyError as e:
        current_app.logger.exception(f"Error when getting id token {json_data}")
        raise KeyError(f"'access_token' {request.json()}") from e

    # Getting Login.gov signing keys for unpacking the id_token correctly.
    jwks = requests.get(certs_url, timeout=5).json()
    public_keys = {
        jwk["kid"]: {
            "key": jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk)),
            "algo": jwk["alg"],
        }
        for jwk in jwks["keys"]
    }
    kid = jwt.get_unverified_header(encoded_id_token)["kid"]
    pub_key = public_keys[kid]["key"]
    algo = public_keys[kid]["algo"]
    id_token = jwt.decode(
        encoded_id_token, pub_key, audience=client_id, algorithms=[algo]
    )
    return id_token
