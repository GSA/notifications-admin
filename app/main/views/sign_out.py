import os
import uuid

import requests
from flask import redirect, url_for, current_app
from flask_login import current_user

from app.main import main


def _sign_out_at_login_dot_gov():

    base_url = "https://idp.int.identitysandbox.gov/openid_connect/logout?"
    client_id = (
        f"client_id={os.getenv('LOGIN_DOT_GOV_CLIENT_ID')}"
    )
    post_logout_redirect_uri = "post_logout_redirect_api=http://localhost:6012/sign-in"
    state = f"state={str(uuid.uuid4())}"

    # TODO If I take this url and put it in the browser, login.gov sign out works properly
    # TODO But with this code it results in a 404 error message and we don't sign out from login.gov
    url = f"{base_url}&{client_id}&{post_logout_redirect_uri}&{state}"
    current_app.logger.info(f"URL={url}")
    response = requests.post(url)
    current_app.logger.info(f"GOT A RESPONSE {response}")


@main.route("/sign-out", methods=(["GET"]))
def sign_out():
    # An AnonymousUser does not have an id
    if current_user.is_authenticated:
        current_user.sign_out()
        _sign_out_at_login_dot_gov()
    return redirect(url_for("main.index"))
