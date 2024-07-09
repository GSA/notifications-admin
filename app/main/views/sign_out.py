import os
from datetime import timedelta

from flask import current_app, make_response, redirect, url_for
from flask_login import current_user

from app.main import main
from app.utils.user import session_clear


@main.route("/sign-out", methods=(["GET", "POST"]))
def sign_out():
    # An AnonymousUser does not have an id
    current_app.logger.info("HIT THE REGULAR SIGN OUT")

    if current_user.is_authenticated:
        # TEMPORARILY RESET THE PERMANENT_SESSION_LIFETIME TO ZERO
        # BUT WE MUST RESET IT IMMEDIATELY AFTER SO AS NOT TO HURT OTHER USERS
        current_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=0)
        session_clear()
        # TODO This doesn't work yet, due to problems above.
        current_user.sign_out()
        login_dot_gov_logout_url = os.getenv("LOGIN_DOT_GOV_LOGOUT_URL")
        if login_dot_gov_logout_url:
            response = make_response(redirect(login_dot_gov_logout_url))
            response.set_cookie(
                "notify_admin_session",
                "",
                expires=0,
                httponly=True,
                secure=True,
                path="/",
            )

            return response
    response = make_response(redirect(url_for("main.index")))
    response.set_cookie(
        "notify_admin_session", "", expires=0, httponly=True, secure=True, path="/"
    )

    return response
