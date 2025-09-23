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
        abort(404, "No invited_org_user")

    form = RegisterUserFromOrgInviteForm(
        invited_org_user,
    )
    form.auth_type.data = "sms_auth"

    if form.validate_on_submit():
        if (
            form.organization.data != invited_org_user.organization
            or form.email_address.data != invited_org_user.email_address
        ):
            abort(400, "organization or email address doesn't match")
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

    invite_data = json.loads(redis_client.get(f"invitedata-{state}").decode("utf8"))
    user_email = redis_client.get(f"user_email-{state}").decode("utf8")
    user_uuid = redis_client.get(f"user_uuid-{state}").decode("utf8")

    # login.gov is going to fail if we don't have at least one of these
    if user_email is None and user_uuid is None:
        flash("Can't find user email and/or uuid")
        abort(403, "Can't find user email and/or uuid")

    invited_user_email_address = redis_client.get(
        f"invited_user_email_address-{state}"
    ).decode("utf8")
    return invite_data, user_email, user_uuid, invited_user_email_address


def put_invite_data_in_redis(
    state, invite_data, user_email, user_uuid, invited_user_email_address
):
    ttl = 2 * 24 * 60 * 60

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
        flash("You cannot accept an invite for another person.")
        abort(403, "You cannot accept an invite for another person #invite")

    if not is_gov_user(user_email):
        flash("You must use a government email address.")
        abort(403, "You must use a government email address #invites")


@main.route("/set-up-your-profile", methods=["GET", "POST"])
@hide_from_search_engines
def set_up_your_profile():

    current_app.logger.info("#invites: Enter set_up_your_profile")
    code = request.args.get("code")
    state = request.args.get("state")

    login_gov_error = request.args.get("error")
    if login_gov_error:
        flash(f"Login.gov error: {login_gov_error}")
        abort(403, f"login_gov_error {login_gov_error} #invites")

    if not state:
        flash("Login.gov state not detected")
        abort(403, "Login.gov state not detected #invites")

    state_key = f"login-state-{unquote(state)}"
    debug_msg(f"Register tries to fetch state_key {state_key}")
    stored_state = unquote(redis_client.get(state_key).decode("utf8"))

    if state != stored_state:
        flash("Internal error: cannot recognize stored state")
        abort(403, "Internal error: cannot recognize stored state #invites")

    user_email = redis_client.get(f"user_email-{state}")
    user_uuid = redis_client.get(f"user_uuid-{state}")

    new_user = user_email is None or user_uuid is None

    if new_user:  # invite path
        current_app.logger.info(
            f"#invites: we are processing a new user with login.gov user_uuid {user_uuid}"
        )
        access_token = sign_in._get_access_token(code)

        user_email, user_uuid = sign_in._get_user_email_and_uuid(access_token)
        current_app.logger.info(
            f"#invites: Got the user_email and user_uuid {user_uuid} from login.gov"
        )
        invite_data = redis_client.get(f"invitedata-{state}")
        # TODO fails here.
        invite_data = json.loads(invite_data)

        is_org_invite, invited_user_id, invited_user_email_address = (
            process_invited_user(invite_data)
        )

        current_app.logger.info(
            f"#invites: does user email match expected? {user_email == invited_user_email_address}"
        )
        check_invited_user_email_address_matches_expected(
            user_email, invited_user_email_address
        )
        if is_org_invite:
            invited_org_user_accept_invite(invited_user_id)
            current_app.logger.info(
                f"#invites: accepted org invite user with invited_user_id \
              {invited_user_id}"
            )

        else:
            invited_user_accept_invite(invited_user_id)
            current_app.logger.info(
                f"#invites: accepted invite user with invited_user_id \
              {invited_user_id}"
            )

        # We need to avoid taking a second trip through the login.gov code because we cannot pull the
        # access token twice.  So once we retrieve these values, let's park them in redis for 15 minutes
        put_invite_data_in_redis(
            state, invite_data, user_email, user_uuid, invited_user_email_address
        )

    form = SetupUserProfileForm()

    if form.validate_on_submit() and not new_user:
        current_app.logger.info("#invites: this is an invite for a pre-existing user")
        invite_data, user_email, user_uuid, invited_user_email_address = (
            get_invite_data_from_redis(state)
        )
        current_app.logger.info(f"#invites: login.gov user_uuid from redis {user_uuid}")

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
            current_app.logger.info(
                f"#invites: registered the new user with login.gov user_uuid {user_uuid}"
            )
        else:
            user.update(mobile_number=form.mobile_number.data, name=form.name.data)
            current_app.logger.info(
                f"#invites: updated the pre-existing user with login.gov user_uuid {user_uuid}"
            )

        # activate the user
        user = user_api_client.get_user_by_uuid_or_email(user_uuid, user_email)
        current_app.logger.info("#invites: going to activate user")
        activate_user(user["id"])
        current_app.logger.info(f"#invites: activated user with user.id {user['id']}")

        if invite_data.get("service_id"):
            usr = User.from_id(user["id"])

            usr.add_to_service(
                invite_data["service_id"],
                invite_data["permissions"],
                invite_data["folder_permissions"],
                invite_data["from_user_id"],
            )

            # notify-admin-1766
            # redirect new users to templates area of new service instead of dashboard
            service_id = invite_data["service_id"]
            url = url_for(".service_dashboard", service_id=service_id)
            url = f"{url}/templates"
            current_app.logger.info(f"#invites redirecting to {url}")
            return redirect(url)
        else:
            usr = User.from_id(user["id"])
            org_id = invite_data["organization"]
            usr.add_to_organization(org_id)
            url = url_for(".organization_dashboard", org_id=org_id)
            current_app.logger.info(f"#invites redirecting to {url}")
            return redirect(url)

    # we take two trips through this method, but should only hit this
    # line on the first trip.  On the second trip, we should get redirected
    # to the accounts page because we have successfully registered.
    return render_template("views/set-up-your-profile.html", form=form)


def get_invited_user_email_address(invited_user_id):
    # InvitedUser is an unhashable type and hard to mock in tests
    # so this convenience method is a workaround for that
    invited_user = InvitedUser.by_id(invited_user_id)
    return invited_user.email_address


def get_invited_org_user_email_address(invited_user_id):
    # InvitedUser is an unhashable type and hard to mock in tests
    # so this convenience method is a workaround for that
    invited_user = InvitedOrgUser.by_id(invited_user_id)
    return invited_user.email_address


def invited_user_accept_invite(invited_user_id):
    invited_user = InvitedUser.by_id(invited_user_id)

    if invited_user.status == InvitedUserStatus.EXPIRED:
        current_app.logger.error("Service invitation has expired")
        flash(
            "Your service invitation has expired; please contact the person who invited you for additional help."
        )
        abort(401, "Your service invitation has expired #invites")

    if invited_user.status == InvitedUserStatus.CANCELLED:
        current_app.logger.error("Service invitation has been cancelled")
        flash(
            "Your service invitation is no longer valid; please contact the person who invited you for additional help."
        )
        abort(401, "Your service invitation was canceled #invites")

    invited_user.accept_invite()


def invited_org_user_accept_invite(invited_user_id):
    invited_user = InvitedOrgUser.by_id(invited_user_id)

    if invited_user.status == InvitedUserStatus.EXPIRED:
        current_app.logger.error("Organization invitation has expired")
        flash(
            "Your organization invitation has expired; please contact the person who invited you for additional help."
        )
        abort(401, "Your organization invitation has expired #invites")

    if invited_user.status == InvitedUserStatus.CANCELLED:
        current_app.logger.error("Organization invitation has been cancelled")
        flash(
            "Your organization invitation is no longer valid; \
                please contact the person who invited you for additional help."
        )
        abort(401, "Your organization invitation was canceled #invites")

    invited_user.accept_invite()


def debug_msg(msg):
    current_app.logger.debug(hilite(msg))


def process_invited_user(invite_data):
    is_org_invite = False
    if invite_data.get("invited_user_id"):
        invited_user_id = invite_data["invited_user_id"]

        invited_user_email_address = get_invited_user_email_address(invited_user_id)
    else:
        invited_user_id = invite_data["id"]
        is_org_invite = True
        invited_user_email_address = get_invited_org_user_email_address(invited_user_id)

    return is_org_invite, invited_user_id, invited_user_email_address
