import os
from datetime import timedelta

from flask import current_app, make_response, redirect, session, url_for
from flask_login import current_user

from app.main import main


@main.route("/sign-out", methods=(["GET", "POST"]))
def sign_out():
    current_app.logger.info("Signing out")
    # For compliance issue #46 we are going to temporarily
    # change the session lifetime to zero for everyone and
    # then immediately set it back to 30 minutes.
    # This seems to be necessary.
    original_lifetime = current_app.config["PERMANENT_SESSION_LIFETIME"]
    if current_user.is_authenticated:
        current_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=0)
        session.clear()

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
            current_app.config["PERMANENT_SESSION_LIFETIME"] = original_lifetime

            return response
    response = make_response(redirect(url_for("main.index")))
    response.set_cookie(
        "notify_admin_session", "", expires=0, httponly=True, secure=True, path="/"
    )
    current_app.config["PERMANENT_SESSION_LIFETIME"] = original_lifetime

    return response
