import os

import requests
from flask import current_app, redirect, session, url_for
from flask_login import current_user

from app.main import main


def _sign_out_at_login_dot_gov():
    base_url = os.getenv("LOGIN_DOT_GOV_BASE_LOGOUT_URL")
    client_id = f"client_id={os.getenv('LOGIN_DOT_GOV_CLIENT_ID')}"
    post_logout_redirect_uri = (
        f"post_logout_redirect_uri={os.getenv('LOGIN_DOT_GOV_SIGNOUT_REDIRECT')}"
    )

    url = f"{base_url}{client_id}&{post_logout_redirect_uri}"
    current_app.logger.info(f"url={url}")

    response = requests.post(url)

    # response = requests.post(url)
    current_app.logger.info(f"login.gov response: {response.text}")


@main.route("/sign-out", methods=(["GET", "POST"]))
def sign_out():

    if current_user.is_authenticated:
        current_user.deactivate()
        session.clear()
        current_user.sign_out()

        session.permanent = False

        login_dot_gov_logout_url = os.getenv("LOGIN_DOT_GOV_LOGOUT_URL")
        if login_dot_gov_logout_url:
            current_app.config["SESSION_PERMANENT"] = False
            return redirect(login_dot_gov_logout_url)
    return redirect(url_for("main.index"))
