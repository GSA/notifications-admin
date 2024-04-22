import json

from flask import abort, current_app, flash, redirect, render_template, session, url_for
from itsdangerous import SignatureExpired
from notifications_utils.url_safe_token import check_token

from app import user_api_client
from app.main import main
from app.main.forms import TwoFactorForm
from app.models.user import User
from app.notify_client import organizations_api_client, service_api_client
from app.utils import hilite
from app.utils.login import redirect_to_sign_in


@main.route("/verify", methods=["GET", "POST"])
@redirect_to_sign_in
def verify():
    user_id = session["user_details"]["id"]

    def _check_code(code):
        return user_api_client.check_verify_code(user_id, code, "sms")

    form = TwoFactorForm(_check_code)

    if form.validate_on_submit():
        session.pop("user_details", None)
        return activate_user(user_id)

    return render_template("views/two-factor-sms.html", form=form)


@main.route("/verify-email/<token>")
def verify_email(token):
    try:
        token_data = check_token(
            token,
            current_app.config["SECRET_KEY"],
            current_app.config["DANGEROUS_SALT"],
            current_app.config["EMAIL_EXPIRY_SECONDS"],
        )
    except SignatureExpired:
        flash(
            "The link in the email we sent you has expired. We've sent you a new one."
        )
        return redirect(url_for("main.resend_email_verification"))

    # token contains json blob of format: {'user_id': '...', 'secret_code': '...'} (secret_code is unused)
    token_data = json.loads(token_data)
    user = User.from_id(token_data["user_id"])
    if not user:
        abort(404)

    if user.is_active:
        flash("That verification link has expired.")
        return redirect(url_for("main.sign_in"))

    if user.email_auth:
        session.pop("user_details", None)
        return activate_user(user.id)

    user.send_verify_code()
    session["user_details"] = {"email": user.email_address, "id": user.id}
    return redirect(url_for("main.verify"))


def activate_user(user_id):
    user = User.from_id(user_id)

    # This is the login.gov path
    try:
        login_gov_invite_data = service_api_client.retrieve_service_invite_data(
            f"service-invite-{user.email_address}"
        )
    except BaseException:  # noqa
        # We will hit an exception if we can't find invite data,
        # but that will be the normal sign in use case
        login_gov_invite_data = None
    if login_gov_invite_data:
        current_app.logger.debug(
            hilite(
                f"uh oh, there was login service invite data {login_gov_invite_data}"
            )
        )
        login_gov_invite_data = json.loads(login_gov_invite_data)
        service_id = login_gov_invite_data["service_id"]
        user_id = user_id
        permissions = login_gov_invite_data["permissions"]
        folder_permissions = login_gov_invite_data["folder_permissions"]

        # Actually call the back end and add the user to the service
        try:
            user_api_client.add_user_to_service(
                service_id, user_id, permissions, folder_permissions
            )
        except BaseException as be:  # noqa
            # TODO if the user is already part of service we should ignore
            current_app.logger.warning(f"Exception adding user to service {be}")

        activated_user = user.activate()
        activated_user.login()
        return redirect(url_for("main.service_dashboard", service_id=service_id))

    try:
        current_app.logger.debug(
            hilite(f"try to get org id with user.email_address {user.email_address}")
        )
        organization_id = organizations_api_client.retrieve_organization_invite_data(
            f"organization-invite-{user.email_address}"
        )
        current_app.logger.debug(hilite(f"organization_id is {organization_id}"))
    except BaseException as be:  # noqa
        current_app.logger.debug(hilite(f"EXCEPTION! {be}"))
        organization_id = None

    if organization_id:

        activated_user = user.activate()
        activated_user.login()
        current_app.logger.debug("Yay, redirecting to org dashbord!")
        return redirect(url_for("main.organization_dashboard", org_id=organization_id))
    else:
        activated_user = user.activate()
        activated_user.login()

        return redirect(url_for("main.add_service", first="first"))


def _add_invited_user_to_service(invitation):
    user = User.from_id(session["user_id"])
    service_id = invitation.service
    user.add_to_service(
        service_id,
        invitation.permissions,
        invitation.folder_permissions,
        invitation.from_user.id,
    )
    return service_id
