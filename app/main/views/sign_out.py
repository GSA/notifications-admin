from datetime import timedelta
import os

import requests
from flask import current_app, make_response, redirect, request, session, url_for
from flask_login import current_user

from app.main import main



@main.route("/sign-out", methods=(["GET", "POST"]))
def sign_out():
    # An AnonymousUser does not have an id
    current_app.logger.info("HIT THE REGULAR SIGN OUT")

    original_lifetime = current_app.config['PERMANENT_SESSION_LIFETIME']
    if current_user.is_authenticated:
        print(f"HERE IS THE SESSION {session}")
        current_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=0)
        session.clear()
        print("SESSION CLEARED")
        # TODO This doesn't work yet, due to problems above.
        current_user.sign_out()
        login_dot_gov_logout_url = os.getenv("LOGIN_DOT_GOV_LOGOUT_URL")
        if login_dot_gov_logout_url:
            response =  make_response(redirect(login_dot_gov_logout_url))
            response.set_cookie('session', '', expires=0, httponly=True, secure=True, path='/')
            current_app.config['PERMANENT_SESSION_LIFETIME'] = original_lifetime

            return response
    response = make_response(redirect(url_for("main.index")))
    response.set_cookie('session', '', expires=0, httponly=True, secure=True, path='/')
    current_app.config['PERMANENT_SESSION_LIFETIME'] = original_lifetime

    return response
