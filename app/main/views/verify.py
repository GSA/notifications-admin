import json

from flask import abort, current_app, flash, redirect, render_template, session, url_for
from itsdangerous import SignatureExpired
from notifications_utils.url_safe_token import check_token

from app import user_api_client
from app.extensions import redis_client
from app.main import main
from app.main.forms import TwoFactorForm
from app.models.user import InvitedOrgUser, InvitedUser, User
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
    login_gov_invite_data = redis_client.raw_get(f"service-invite-{user.email_address}")
    if login_gov_invite_data:
        login_gov_invite_data = json.loads(login_gov_invite_data.decode("utf8"))
    current_app.logger.info(hilite(f"LOGIN_GOV_INVITE_DATA {login_gov_invite_data}"))

    # This is the deprecated path for organization invites where we get id from session
    session["current_session_id"] = user.current_session_id
    organization_id = session.get("organization_id")

    activated_user = user.activate()
    activated_user.login()

    # TODO when login.gov is mandatory, get rid of the if clause, it is deprecated.
    invited_user = InvitedUser.from_session()
    if invited_user:
        service_id = _add_invited_user_to_service(invited_user)
        return redirect(url_for("main.service_dashboard", service_id=service_id))
    elif login_gov_invite_data:
        service_id = login_gov_invite_data["service_id"]
        current_app.logger.info(hilite(f"SERVICE_ID={service_id}"))

        user.add_to_service(
            service_id,
            login_gov_invite_data["permissions"],
            login_gov_invite_data["folder_permissions"],
            login_gov_invite_data["from_user_id"],
        )
        return redirect(url_for("main.service_dashboard", service_id=service_id))

    # TODO when login.gov is mandatory, git rid of the if clause, it is deprecated.
    invited_org_user = InvitedOrgUser.from_session()
    if invited_org_user:
        user_api_client.add_user_to_organization(invited_org_user.organization, user_id)
    elif redis_client.raw_get(f"organization-invite-{user.email_address}"):
        organization_id = redis_client.raw_get(
            f"organization-invite-{user.email_address}"
        )
        current_app.logger.info(hilite(f"ORGANIZATION_ID FROM REDIS {organization_id}"))
        user_api_client.add_user_to_organization(
            organization_id.decode("utf8"), user_id
        )

    if organization_id:
        return redirect(url_for("main.organization_dashboard", org_id=organization_id))
    else:
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
