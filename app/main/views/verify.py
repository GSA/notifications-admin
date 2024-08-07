import json

from flask import abort, current_app, flash, redirect, render_template, session, url_for
from itsdangerous import SignatureExpired

from app import user_api_client
from app.main import main
from app.main.forms import TwoFactorForm
from app.models.user import User
from app.utils.login import redirect_to_sign_in
from notifications_utils.url_safe_token import check_token


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
        current_app.logger.error("Email link expired #notify-admin-1505")
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
        current_app.logger.error(
            f"User is using an invite link but is already logged in {user.id} #notify-admin-1505"
        )
        flash("That verification link has expired.")
        return redirect(url_for("main.sign_in"))

    if user.email_auth:
        session.pop("user_details", None)
        return activate_user(user.id)

    user.send_verify_code()
    session["user_details"] = {"email": user.email_address, "id": user.id}
    current_app.logger.info(f"Email verified for user {user.id} #notify-admin-1505")
    return redirect(url_for("main.verify"))


def activate_user(user_id):
    user = User.from_id(user_id)

    # TODO add org invites back in the new way
    # organization_id = redis_client.get(
    #   f"organization-invite-{user.email_address}"
    # )
    # user_api_client.add_user_to_organization(
    #   organization_id.decode("utf8"), user_id
    # )
    organization_id = None

    if organization_id:
        return redirect(url_for("main.organization_dashboard", org_id=organization_id))
    else:
        activated_user = user.activate()
        current_app.logger.info(f"Activated user {user.id} #notify-admin-1505")
        activated_user.login()
        current_app.logger.info(f"Logged in user {user.id} #notify-admin-1505")
        return redirect(url_for("main.add_service", first="first"))
