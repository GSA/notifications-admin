import os
import time
import uuid

import jwt
import requests
from flask import (
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user

from app import login_manager, user_api_client
from app.main import main
from app.main.views.index import error
from app.main.views.verify import activate_user
from app.models.user import User
from app.utils import hide_from_search_engines
from app.utils.login import is_safe_redirect_url
from app.utils.time import is_less_than_days_ago
from app.utils.user import is_gov_user
from notifications_utils.url_safe_token import generate_token


def _reformat_keystring(orig):
    arr = orig.split("-----")
    begin = arr[1]
    end = arr[3]
    middle = arr[2].strip()
    new_keystring = f"-----{begin}-----\n{middle}\n-----{end}-----\n"
    return new_keystring


def _get_access_token(code, state):
    client_id = os.getenv("LOGIN_DOT_GOV_CLIENT_ID")
    access_token_url = os.getenv("LOGIN_DOT_GOV_ACCESS_TOKEN_URL")
    keystring = os.getenv("LOGIN_PEM")
    if " " in keystring:
        keystring = _reformat_keystring(keystring)

    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": access_token_url,
        "jti": str(uuid.uuid4()),
        # JWT expiration time (10 minute maximum)
        "exp": int(time.time()) + (10 * 60),
    }
    token = jwt.encode(payload, keystring, algorithm="RS256")
    base_url = f"{access_token_url}?"
    cli_assert = f"client_assertion={token}"
    cli_assert_type = "client_assertion_type=urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion-type%3Ajwt-bearer"
    code_param = f"code={code}"
    url = f"{base_url}{cli_assert}&{cli_assert_type}&{code_param}&grant_type=authorization_code"
    headers = {"Authorization": "Bearer %s" % token}
    response = requests.post(url, headers=headers)
    if response.json().get("access_token") is None:
        # Capture the response json here so it hopefully shows up in error reports
        current_app.logger.error(
            f"Error when getting access token {response.json()} #notify-admin-1505"
        )
        raise KeyError(f"'access_token' {response.json()}")
    access_token = response.json()["access_token"]
    return access_token


def _get_user_email_and_uuid(access_token):
    headers = {"Authorization": "Bearer %s" % access_token}
    user_info_url = os.getenv("LOGIN_DOT_GOV_USER_INFO_URL")
    user_attributes = requests.get(
        user_info_url,
        headers=headers,
    )
    user_email = user_attributes.json()["email"]
    user_uuid = user_attributes.json()["sub"]
    return user_email, user_uuid


def _do_login_dot_gov():
    # start login.gov
    code = request.args.get("code")
    state = request.args.get("state")
    login_gov_error = request.args.get("error")

    if login_gov_error:
        current_app.logger.error(
            f"login.gov error: {login_gov_error} #notify-admin-1505"
        )
        raise Exception(f"Could not login with login.gov {login_gov_error}")
    elif code and state:

        # activate the user
        try:
            access_token = _get_access_token(code, state)
            user_email, user_uuid = _get_user_email_and_uuid(access_token)
            if not is_gov_user(user_email):
                current_app.logger.error(
                    "invited user has a non-government email address. #notify-admin-1505"
                )
                flash("You must use a government email address.")
                abort(403)
            redirect_url = request.args.get("next")
            user = user_api_client.get_user_by_uuid_or_email(user_uuid, user_email)
            current_app.logger.info(
                f"Retrieved user {user['id']} from db #notify-admin-1505"
            )

            # Check if the email needs to be revalidated
            is_fresh_email = is_less_than_days_ago(
                user["email_access_validated_at"], 90
            )
            if not is_fresh_email:
                return verify_email(user, redirect_url)

            usr = User.from_email_address(user["email_address"])
            current_app.logger.info(f"activating user {usr.id} #notify-admin-1505")
            activate_user(usr.id)
        except BaseException as be:  # noqa B036
            current_app.logger.error(f"Error signing in: {be} #notify-admin-1505 ")
            error(401)
        return redirect(url_for("main.show_accounts_or_dashboard", next=redirect_url))

    # end login.gov


def verify_email(user, redirect_url):
    user_api_client.send_verify_code(user["id"], "email", None, redirect_url)
    title = "Email resent" if request.args.get("email_resent") else "Check your email"
    redirect_url = request.args.get("next")
    return render_template(
        "views/re-validate-email-sent.html", title=title, redirect_url=redirect_url
    )


def _handle_e2e_tests(redirect_url):
    try:
        current_app.logger.warning("E2E TESTS ARE ENABLED.")
        current_app.logger.warning(
            "If you are getting a 404 on signin, comment out E2E vars in .env file!"
        )
        user = user_api_client.get_user_by_email(os.getenv("NOTIFY_E2E_TEST_EMAIL"))
        activate_user(user["id"])
        return redirect(
            url_for(
                "main.show_accounts_or_dashboard",
                next="EMAIL_IS_OK",
            )
        )
    except Exception as e:
        stre = str(e)
        stre = stre.replace(" ", "_")
        # Trying to get a message back to playwright somehow since we can't see the admin logs
        return redirect(url_for(f"https://{stre}"))

    # return redirect(url_for("main.show_accounts_or_dashboard", next=redirect_url))


@main.route("/sign-in", methods=(["GET", "POST"]))
@hide_from_search_engines
def sign_in():

    # If we have to revalidated the email, send the message
    # via email and redirect to the "verify your email page"
    # and don't proceed further with login
    redirect_url = request.args.get("next")

    # if os.getenv("NOTIFY_E2E_TEST_EMAIL"):
    return _handle_e2e_tests(None)

    email_verify_template = _do_login_dot_gov()
    if (
        email_verify_template
        and not isinstance(email_verify_template, Response)
        and "Check your email" in email_verify_template
    ):
        return email_verify_template

    if current_user and current_user.is_authenticated:
        if redirect_url and is_safe_redirect_url(redirect_url):
            return redirect(redirect_url)
        return redirect(url_for("main.show_accounts_or_dashboard"))

    token = generate_token(
        str(request.remote_addr),
        current_app.config["SECRET_KEY"],
        current_app.config["DANGEROUS_SALT"],
    )
    url = os.getenv("LOGIN_DOT_GOV_INITIAL_SIGNIN_URL")
    # handle unit tests
    if url is not None:
        url = url.replace("NONCE", token)
        url = url.replace("STATE", token)
    return render_template(
        "views/signin.html",
        again=bool(redirect_url),
        initial_signin_url=url,
    )


@login_manager.unauthorized_handler
def sign_in_again():
    return redirect(url_for("main.sign_in", next=request.path))
