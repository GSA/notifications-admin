import base64
import json
import uuid
from datetime import datetime, timedelta

from flask import (
    abort,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user

from app import user_api_client
from app.main import main
from app.main.forms import (
    RegisterUserForm,
    RegisterUserFromInviteForm,
    RegisterUserFromOrgInviteForm,
    SetupUserProfileForm,
)
from app.main.views import sign_in
from app.main.views.verify import activate_user
from app.models.service import Service
from app.models.user import InvitedOrgUser, InvitedUser, User
from app.utils import hide_from_search_engines, hilite


@main.route("/register", methods=["GET", "POST"])
@hide_from_search_engines
def register():
    if current_user and current_user.is_authenticated:
        return redirect(url_for("main.show_accounts_or_dashboard"))

    form = RegisterUserForm()
    if form.validate_on_submit():
        _do_registration(form, send_sms=False)
        return redirect(url_for("main.registration_continue"))

    return render_template("views/register.html", form=form)


@main.route("/register-from-invite", methods=["GET", "POST"])
def register_from_invite():
    invited_user = InvitedUser.from_session()
    if not invited_user:
        abort(404)

    form = RegisterUserFromInviteForm(invited_user)

    if form.validate_on_submit():
        if (
            form.service.data != invited_user.service
            or form.email_address.data != invited_user.email_address
        ):
            abort(400)
        _do_registration(form, send_email=False, send_sms=invited_user.sms_auth)
        invited_user.accept_invite()
        if invited_user.sms_auth:
            return redirect(url_for("main.verify"))
        else:
            # we've already proven this user has email because they clicked the invite link,
            # so just activate them straight away
            return activate_user(session["user_details"]["id"])

    return render_template(
        "views/register-from-invite.html", invited_user=invited_user, form=form
    )


@main.route("/register-from-org-invite", methods=["GET", "POST"])
def register_from_org_invite():
    invited_org_user = InvitedOrgUser.from_session()
    if not invited_org_user:
        abort(404)

    form = RegisterUserFromOrgInviteForm(
        invited_org_user,
    )
    form.auth_type.data = "sms_auth"

    if form.validate_on_submit():
        if (
            form.organization.data != invited_org_user.organization
            or form.email_address.data != invited_org_user.email_address
        ):
            abort(400)
        _do_registration(
            form,
            send_email=False,
            send_sms=True,
            organization_id=invited_org_user.organization,
        )
        invited_org_user.accept_invite()

        return redirect(url_for("main.verify"))
    return render_template(
        "views/register-from-org-invite.html",
        invited_org_user=invited_org_user,
        form=form,
    )


def _do_registration(form, send_sms=True, send_email=True, organization_id=None):
    user = User.from_email_address_or_none(form.email_address.data)
    if user:
        if send_email:
            user.send_already_registered_email()
        session["expiry_date"] = str(datetime.utcnow() + timedelta(hours=1))
        session["user_details"] = {"email": user.email_address, "id": user.id}
    else:
        user = User.register(
            name=form.name.data,
            email_address=form.email_address.data,
            mobile_number=form.mobile_number.data,
            password=form.password.data,
            auth_type=form.auth_type.data,
        )

        if send_email:
            user.send_verify_email()

        if send_sms:
            user.send_verify_code()
        session["expiry_date"] = str(datetime.utcnow() + timedelta(hours=1))
        session["user_details"] = {"email": user.email_address, "id": user.id}
    if organization_id:
        session["organization_id"] = organization_id


@main.route("/registration-continue")
def registration_continue():
    if not session.get("user_details"):
        return redirect(url_for(".show_accounts_or_dashboard"))
    else:
        raise Exception("Unexpected routing in registration_continue")


@main.route("/set-up-your-profile", methods=["GET", "POST"])
@hide_from_search_engines
def set_up_your_profile():

    form = SetupUserProfileForm()

    if form.validate_on_submit():
        # start login.gov
        code = request.args.get("code")
        state = request.args.get("state")
        login_gov_error = request.args.get("error")
        if code and state:
            access_token = sign_in._get_access_token(code, state)
            user_email, user_uuid = sign_in._get_user_email_and_uuid(access_token)

            invite_data = state.encode("utf8")
            invite_data = base64.b64decode(invite_data)
            invite_data = json.loads(invite_data)
            invited_service = Service.from_id(invite_data["service_id"])
            invited_user_id = invite_data["invited_user_id"]
            invited_user = InvitedUser.by_id(invited_user_id)
            current_app.logger.debug(
                hilite(
                    f"INVITED USER {invited_user.email_address} to service {invited_service.name}"
                )
            )
            invited_user.accept_invite()
            current_app.logger.debug(hilite("ACCEPTED INVITE"))

        elif login_gov_error:
            current_app.logger.error(f"login.gov error: {login_gov_error}")
            raise Exception(f"Could not login with login.gov {login_gov_error}")
        # end login.gov

        # create the user
        # TODO we have to provide something for password until that column goes away
        # TODO ideally we would set the user's preferred timezone here as well

        user = user_api_client.get_user_by_uuid_or_email(user_uuid, user_email)
        if user is None:
            user = User.register(
                name=form.name.data,
                email_address=user_email,
                mobile_number=form.mobile_number.data,
                password=str(uuid.uuid4()),
                auth_type="sms_auth",
            )

        # activate the user
        user = user_api_client.get_user_by_uuid_or_email(user_uuid, user_email)
        activate_user(user["id"])
        usr = User.from_id(user["id"])
        usr.add_to_service(
            invited_service.id,
            invite_data["permissions"],
            invite_data["folder_permissions"],
            invite_data["from_user_id"],
        )
        current_app.logger.debug(
            hilite(f"Added user {usr.email_address} to service {invited_service.name}")
        )
        return redirect(url_for("main.show_accounts_or_dashboard"))

    return render_template("views/set-up-your-profile.html", form=form)
