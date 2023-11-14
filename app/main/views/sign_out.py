import os

import requests
from flask import current_app, redirect, url_for
from flask_login import current_user

from app.main import main

# ask login.gov if we really need manual logout and what's up with one hour sessions
# ask login.gov how they recommend approaching dev environment
# ask Tim Donaworth the same for #2



def _sign_out_at_login_dot_gov():
    base_url = "https://idp.int.identitysandbox.gov/openid_connect/logout?"
    client_id = f"client_id={os.getenv('LOGIN_DOT_GOV_CLIENT_ID')}"
    post_logout_redirect_uri = "post_logout_redirect_uri=http://localhost:6012/sign-out"

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
    
        return redirect("https://idp.int.identitysandbox.gov/openid_connect/logout?client_id=urn:gov:gsa:openidconnect.profiles:sp:sso:gsa:test_notify_gov&post_logout_redirect_uri=http://localhost:6012/sign-out")
    return redirect(url_for("main.index"))


@main.route("/sign-out-at-login-gov", methods=(["POST"]))
def sign_out_at_login_gov():
    current_app.logger.info("SHOULD BE REDIRECTING TO LOGIN GOV")
    return redirect("https://idp.int.identitysandbox.gov/openid_connect/logout?client_id=urn:gov:gsa:openidconnect.profiles:sp:sso:gsa:test_notify_gov&post_logout_redirect_uri=http://localhost:6012/sign-out")
