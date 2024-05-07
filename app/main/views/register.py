import base64
import json
import uuid
from datetime import datetime, timedelta

from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user

from app import user_api_client
from app.main import main
from app.main.forms import (  # RegisterUserFromInviteForm,
    RegisterUserForm,
    RegisterUserFromOrgInviteForm,
    SetupUserProfileForm,
)
from app.main.views import sign_in
from app.main.views.verify import activate_user
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


@main.route("/register-from-org-invite", methods=["GET", "POST"])
# TODO This is deprecated, we are now handling invites in the
# login.gov workflow.  Leaving it here until we write the new
# org registration.
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
            return _handle_login_dot_gov_invite(code, state, form)
        elif login_gov_error:
            current_app.logger.error(f"login.gov error: {login_gov_error}")
            raise Exception(f"Could not login with login.gov {login_gov_error}")
        # end login.gov

    return render_template("views/set-up-your-profile.html", form=form)


def get_invited_user_email_address(invited_user_id):
    # InvitedUser is an unhashable type and hard to mock in tests
    # so this convenience method is a workaround for that
    invited_user = InvitedUser.by_id(invited_user_id)
    return invited_user.email_address


def invited_user_accept_invite(invited_user_id):
    # InvitedUser is an unhashable type and hard to mock in tests
    # so this convenience method is a workaround for that
    invited_user = InvitedUser.by_id(invited_user_id)
    invited_user.accept_invite()


def debug_msg(msg):
    current_app.logger.debug(hilite(msg))


def _handle_login_dot_gov_invite(code, state, form):
    debug_msg(f"enter _handle_login_dot_gov_invite with code {code} state {state}")
    access_token = sign_in._get_access_token(code, state)
    debug_msg("Got the access token for login.gov")
    user_email, user_uuid = sign_in._get_user_email_and_uuid(access_token)
    debug_msg(
        f"Got the user_email {user_email} and user_uuid {user_uuid} from login.gov"
    )
    debug_msg(f"raw state {state}")
    invite_data = state.encode("utf8")
    debug_msg(f"utf8 encoded state {invite_data}")
    invite_data = base64.b64decode(invite_data)
    debug_msg(f"b64 decoded state {invite_data}")
    invite_data = json.loads(invite_data)
    debug_msg(f"final state {invite_data}")
    invited_user_id = invite_data["invited_user_id"]
    invited_user_email_address = get_invited_user_email_address(invited_user_id)
    debug_msg(f"email address from the invite_date is {invited_user_email_address}")
    if user_email.lower() != invited_user_email_address.lower():
        debug_msg("invited user email did not match expected email, abort(403)")
        flash("You cannot accept an invite for another person.")
        session.pop("invited_user_id", None)
        abort(403)
    else:
        invited_user_accept_invite(invited_user_id)
        debug_msg(
            f"invited user {invited_user_email_address} to service {invite_data['service_id']}"
        )
        debug_msg("accepted invite")
        user = user_api_client.get_user_by_uuid_or_email(user_uuid, user_email)
        if user is None:
            user = User.register(
                name=form.name.data,
                email_address=user_email,
                mobile_number=form.mobile_number.data,
                password=str(uuid.uuid4()),
                auth_type="sms_auth",
            )
            debug_msg(f"registered user {form.name.data} with email {user_email}")

        # activate the user
        user = user_api_client.get_user_by_uuid_or_email(user_uuid, user_email)
        activate_user(user["id"])
        debug_msg("activated user")
        usr = User.from_id(user["id"])
        usr.add_to_service(
            invite_data["service_id"],
            invite_data["permissions"],
            invite_data["folder_permissions"],
            invite_data["from_user_id"],
        )
        debug_msg(
            f"Added user {usr.email_address} to service {invite_data['service_id']}"
        )
        return redirect(url_for("main.show_accounts_or_dashboard"))
