import os

import requests
from flask import current_app, redirect, url_for
from flask_login import current_user

from app.main import main

# ask login.gov if we really need manual logout and what's up with one hour sessions
# ask login.gov how they recommend approaching dev environment
# ask Tim Donaworth the same for #2


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
    # An AnonymousUser does not have an id
    current_app.logger.info("HIT THE REGULAR SIGN OUT")
    if current_user.is_authenticated:
        # TODO This doesn't work yet, due to problems above.
        current_user.sign_out()

        return redirect(os.getenv("LOGIN_DOT_GOV_LOGOUT_URL"))
    return redirect(url_for("main.index"))
