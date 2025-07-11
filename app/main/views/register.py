import json
import uuid
from datetime import datetime, timedelta
from urllib.parse import unquote

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

from app import redis_client, user_api_client
from app.enums import InvitedUserStatus
from app.main import main
from app.main.forms import (
    RegisterUserFromOrgInviteForm,
    SetupUserProfileForm,
)
from app.main.views import sign_in
from app.main.views.verify import activate_user
from app.models.user import InvitedOrgUser, InvitedUser, User
from app.utils import hide_from_search_engines, hilite
from app.utils.user import is_gov_user


@main.route("/register", methods=["GET", "POST"])
@hide_from_search_engines
def register():
    abort(404)


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
    abort(404)


def get_invite_data_from_redis(state):

    invite_data = json.loads(redis_client.get(f"invitedata-{state}"))
    user_email = redis_client.get(f"user_email-{state}").decode("utf8")
    user_uuid = redis_client.get(f"user_uuid-{state}").decode("utf8")
    invited_user_email_address = redis_client.get(
        f"invited_user_email_address-{state}"
    ).decode("utf8")
    return invite_data, user_email, user_uuid, invited_user_email_address


def put_invite_data_in_redis(
    state, invite_data, user_email, user_uuid, invited_user_email_address
):
    ttl = 60 * 15  # 15 minutes

    redis_client.set(f"invitedata-{state}", json.dumps(invite_data), ex=ttl)
    redis_client.set(f"user_email-{state}", user_email, ex=ttl)
    redis_client.set(f"user_uuid-{state}", user_uuid, ex=ttl)
    redis_client.set(
        f"invited_user_email_address-{state}",
        invited_user_email_address,
        ex=ttl,
    )


def check_invited_user_email_address_matches_expected(
    user_email, invited_user_email_address
):
    if user_email.lower() != invited_user_email_address.lower():
        debug_msg("invited user email did not match expected email, abort(403)")
        flash("You cannot accept an invite for another person.")
        abort(403)

    if not is_gov_user(user_email):
        debug_msg("invited user has a non-government email address.")
        flash("You must use a government email address.")
        abort(403)


@main.route("/set-up-your-profile", methods=["GET", "POST"])
@hide_from_search_engines
def set_up_your_profile():

    debug_msg(f"Enter set_up_your_profile with request.args {request.args}")
    code = request.args.get("code")
    state = request.args.get("state")

    state_key = f"login-state-{unquote(state)}"
    stored_state = unquote(redis_client.get(state_key).decode("utf8"))
    if state != stored_state:
        current_app.logger.error(f"State Error: {state} != {stored_state}")
        abort(403)

    login_gov_error = request.args.get("error")

    user_email = redis_client.get(f"user_email-{state}")
    user_uuid = redis_client.get(f"user_uuid-{state}")

    new_user = user_email is None or user_uuid is None

    if new_user:  # invite path
        access_token = sign_in._get_access_token(code)

        debug_msg("Got the access token for login.gov")
        user_email, user_uuid = sign_in._get_user_email_and_uuid(access_token)
        debug_msg(
            f"Got the user_email {user_email} and user_uuid {user_uuid} from login.gov"
        )
        invite_data = redis_client.get(f"invitedata-{state}")
        invite_data = json.loads(invite_data)
        debug_msg(f"final state {invite_data}")
        invited_user_id = invite_data["invited_user_id"]
        invited_user_email_address = get_invited_user_email_address(invited_user_id)
        debug_msg(f"email address from the invite_date is {invited_user_email_address}")
        check_invited_user_email_address_matches_expected(
            user_email, invited_user_email_address
        )

        invited_user_accept_invite(invited_user_id)
        debug_msg(
            f"accepted invite user {invited_user_email_address} to service {invite_data['service_id']}"
        )
        # We need to avoid taking a second trip through the login.gov code because we cannot pull the
        # access token twice.  So once we retrieve these values, let's park them in redis for 15 minutes
        put_invite_data_in_redis(
            state, invite_data, user_email, user_uuid, invited_user_email_address
        )

    form = SetupUserProfileForm()

    if form.validate_on_submit() and not new_user:
        invite_data, user_email, user_uuid, invited_user_email_address = (
            get_invite_data_from_redis(state)
        )

        # create or update the user
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
        else:
            user.update(mobile_number=form.mobile_number.data, name=form.name.data)
            debug_msg(f"updated user {form.name.data}")

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
        # notify-admin-1766
        # redirect new users to templates area of new service instead of dashboard
        service_id = invite_data["service_id"]
        url = url_for(".service_dashboard", service_id=service_id)
        url = f"{url}/templates"
        return redirect(url)

    elif login_gov_error:
        current_app.logger.error(f"login.gov error: {login_gov_error}")
        abort(403)

    # we take two trips through this method, but should only hit this
    # line on the first trip.  On the second trip, we should get redirected
    # to the accounts page because we have successfully registered.
    return render_template("views/set-up-your-profile.html", form=form)


def get_invited_user_email_address(invited_user_id):
    # InvitedUser is an unhashable type and hard to mock in tests
    # so this convenience method is a workaround for that
    invited_user = InvitedUser.by_id(invited_user_id)
    return invited_user.email_address


def invited_user_accept_invite(invited_user_id):
    invited_user = InvitedUser.by_id(invited_user_id)

    if invited_user.status == InvitedUserStatus.EXPIRED:
        current_app.logger.error("User invitation has expired")
        flash(
            "Your invitation has expired; please contact the person who invited you for additional help."
        )
        abort(401)

    if invited_user.status == InvitedUserStatus.CANCELLED:
        current_app.logger.error("User invitation has been cancelled")
        flash(
            "Your invitation is no longer valid; please contact the person who invited you for additional help."
        )
        abort(401)

    invited_user.accept_invite()


def debug_msg(msg):
    current_app.logger.debug(hilite(msg))
