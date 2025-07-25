from flask import abort, flash, redirect, render_template, session, url_for
from flask_login import current_user
from markupsafe import Markup

from app.enums import (
    AuthType,
    InvitedOrgUserStatus,
    InvitedUserStatus,
    ServicePermission,
)
from app.main import main
from app.models.organization import Organization
from app.models.service import Service
from app.models.user import InvitedOrgUser, InvitedUser, OrganizationUsers, User, Users


@main.route("/invitation/<token>")
def accept_invite(token):
    invited_user = InvitedUser.from_token(token)

    if (
        not current_user.is_anonymous
        and current_user.email_address.lower() != invited_user.email_address.lower()
    ):
        message = Markup(
            f"""
            You’re signed in as {current_user.email_address}.
            This invite is for another email address.
            <a href={url_for("main.sign_out")} class="usa-link">Sign out</a>
            and click the link again to accept this invite.
            """
        )  # nosec

        flash(message=message)

        abort(403)

    if invited_user.status == InvitedUserStatus.CANCELLED:
        service = Service.from_id(invited_user.service)
        return render_template(
            "views/cancelled-invitation.html",
            from_user=invited_user.from_user.name,
            service_name=service.name,
        )
    if invited_user.status == InvitedUserStatus.ACCEPTED:
        session.pop("invited_user_id", None)
        service = Service.from_id(invited_user.service)
        return redirect(
            url_for("main.service_dashboard", service_id=invited_user.service)
        )

    session["invited_user_id"] = invited_user.id

    existing_user = User.from_email_address_or_none(invited_user.email_address)

    if existing_user:
        existing_user.update_email_access_validated_at()
        invited_user.accept_invite()
        if existing_user in Users(invited_user.service):
            return redirect(
                url_for("main.service_dashboard", service_id=invited_user.service)
            )
        else:
            service = Service.from_id(invited_user.service)
            # if the service you're being added to can modify auth type, then check if we can do this;
            # if the user is a Platform Admin, we silently leave this unchanged to prevent a security
            # issue where someone could switch their auth type to something less secure
            if (
                service.has_permission(ServicePermission.EMAIL_AUTH)
                and not existing_user.platform_admin
            ):
                if invited_user.auth_type == AuthType.EMAIL_AUTH or (
                    # they have a phone number, we want them to start using it.
                    # if they dont have a mobile we just ignore that option of the invite
                    existing_user.mobile_number
                    and invited_user.auth_type == "sms_auth"
                ):
                    existing_user.update(auth_type=invited_user.auth_type)
            existing_user.add_to_service(
                service_id=invited_user.service,
                permissions=invited_user.permissions,
                folder_permissions=invited_user.folder_permissions,
                invited_by_id=invited_user.from_user.id,
            )
            return redirect(url_for("main.service_dashboard", service_id=service.id))
    else:
        return redirect(url_for("main.register_from_invite"))


@main.route("/organization-invitation/<token>")
def accept_org_invite(token):
    invited_org_user = InvitedOrgUser.from_token(token)

    if (
        not current_user.is_anonymous
        and current_user.email_address.lower() != invited_org_user.email_address.lower()
    ):
        message = Markup(
            """
            You’re signed in as {}.
            This invite is for another email address.
            <a class="usa-link" href={}>Sign out</a>
            and click the link again to accept this invite.
            """.format(
                current_user.email_address, url_for("main.sign_out")
            )
        )  # nosec

        flash(message=message)

        abort(403)

    if invited_org_user.status == InvitedOrgUserStatus.CANCELLED:
        organization = Organization.from_id(invited_org_user.organization)
        return render_template(
            "views/cancelled-invitation.html",
            from_user=invited_org_user.invited_by.name,
            organization_name=organization.name,
        )

    if invited_org_user.status == InvitedOrgUserStatus.ACCEPTED:
        session.pop("invited_org_user_id", None)
        return redirect(
            url_for("main.organization_dashboard", org_id=invited_org_user.organization)
        )

    session["invited_org_user_id"] = invited_org_user.id

    existing_user = User.from_email_address_or_none(invited_org_user.email_address)
    organization_users = OrganizationUsers(invited_org_user.organization)

    if existing_user:
        existing_user.update_email_access_validated_at()
        invited_org_user.accept_invite()
        if existing_user not in organization_users:
            existing_user.add_to_organization(
                organization_id=invited_org_user.organization
            )
        return redirect(
            url_for("main.organization_dashboard", org_id=invited_org_user.organization)
        )
    else:
        return redirect(url_for("main.register_from_org_invite"))
