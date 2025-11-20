import re
from collections import OrderedDict
from datetime import datetime
from functools import partial

from flask import (
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user
from markupsafe import escape

from app import (
    current_organization,
    org_invite_api_client,
    organizations_client,
    service_api_client,
)
from app.enums import OrganizationType
from app.event_handlers import create_archive_service_event
from app.formatters import email_safe
from app.main import main
from app.main.forms import (
    AdminBillingDetailsForm,
    AdminNewOrganizationForm,
    AdminNotesForm,
    AdminOrganizationDomainsForm,
    CreateServiceForm,
    InviteOrgUserForm,
    OrganizationOrganizationTypeForm,
    RenameOrganizationForm,
    SearchByNameForm,
    SearchUsersForm,
)
from app.main.views.add_service import _create_service
from app.main.views.dashboard import (
    get_tuples_of_financial_years,
    requested_and_current_financial_year,
)
from app.models.organization import AllOrganizations, Organization
from app.models.service import Service
from app.models.user import InvitedOrgUser, User
from app.notify_client import cache
from app.utils.csv import Spreadsheet
from app.utils.user import user_has_permissions, user_is_platform_admin
from notifications_python_client.errors import HTTPError

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@main.route("/organizations", methods=["GET"])
@user_is_platform_admin
def organizations():
    return render_template(
        "views/organizations/index.html",
        organizations=AllOrganizations(),
        search_form=SearchByNameForm(),
    )


@main.route("/organizations/add", methods=["GET", "POST"])
@user_is_platform_admin
def add_organization():
    form = AdminNewOrganizationForm()

    if form.validate_on_submit():
        try:
            return redirect(
                url_for(
                    ".organization_settings",
                    org_id=Organization.create_from_form(form).id,
                )
            )
        except HTTPError as e:
            msg = "Organization name already exists"
            if e.status_code == 400 and msg in e.message:
                form.name.errors.append("This organization name is already in use")
            else:
                raise e

    return render_template("views/organizations/add-organization.html", form=form)


def get_organization_message_allowance(org_id):
    try:
        message_usage = organizations_client.get_organization_message_usage(org_id)
    except Exception as e:
        current_app.logger.error(f"Error fetching organization message usage: {e}")
        message_usage = {}

    return {
        "messages_sent": message_usage.get("messages_sent", 0),
        "messages_remaining": message_usage.get("messages_remaining", 0),
        "total_message_limit": message_usage.get("total_message_limit", 0),
    }


def _handle_create_service(org_id):
    create_service_form = CreateServiceForm(
        organization_type=current_user.default_organization_type
        or OrganizationType.FEDERAL
    )

    if request.method == "POST" and create_service_form.validate_on_submit():
        service_name = create_service_form.name.data
        service_id, error = _create_service(
            service_name,
            create_service_form.organization_type.data,
            email_safe(service_name),
            create_service_form,
        )
        if not error:
            current_organization.associate_service(service_id)
            flash(f"Service '{service_name}' has been created", "default_with_tick")
            session["new_service_id"] = service_id
            return redirect(url_for(".organization_dashboard", org_id=org_id))
        else:
            flash("Error creating service", "error")

    return create_service_form


def _handle_invite_user(org_id):
    invite_user_form = InviteOrgUserForm(
        inviter_email_address=current_user.email_address
    )

    if request.method == "POST" and invite_user_form.validate_on_submit():
        try:
            invited_org_user = InvitedOrgUser.create(
                current_user.id, org_id, invite_user_form.email_address.data
            )
            flash(
                f"Invite sent to {invited_org_user.email_address}",
                "default_with_tick",
            )
            return redirect(url_for(".organization_dashboard", org_id=org_id))
        except Exception:
            flash("Error sending invitation", "error")

    return invite_user_form


def _handle_edit_service(org_id, service_id):
    service = Service.from_id(service_id)

    if request.method == "POST":
        service_name = request.form.get("service_name", "").strip()
        primary_contact = request.form.get("primary_contact", "").strip()
        new_status = request.form.get("status")

        if not service_name:
            flash("Service name is required", "error")
        elif primary_contact and not EMAIL_REGEX.match(primary_contact):
            flash("Please enter a valid email address", "error")
        else:
            if service_name != service.name:
                service.update(name=service_name)

            if primary_contact != (service.billing_contact_email_addresses or ""):
                service.update(billing_contact_email_addresses=primary_contact)

            current_status = "trial" if service.trial_mode else "live"
            if new_status != current_status:
                service.update_status(live=(new_status == "live"))
                cache.redis_client.delete("organizations")

            flash("Service updated successfully", "default_with_tick")
            session["updated_service_id"] = str(service_id)
            return redirect(url_for(".organization_dashboard", org_id=org_id))

    return {
        "id": service.id,
        "name": (
            escape(request.form.get("service_name", "").strip())
            if request.method == "POST"
            else service.name
        ),
        "primary_contact": (
            escape(request.form.get("primary_contact", "").strip())
            if request.method == "POST"
            else (service.billing_contact_email_addresses or "")
        ),
        "status": "trial" if service.trial_mode else "live",
    }


def _handle_delete_service(org_id, service_id):
    if request.method != "POST":
        flash("Invalid request method", "error")
        return redirect(url_for(".organization_dashboard", org_id=org_id))

    service = Service.from_id(service_id)

    if not service.active or not (service.trial_mode or current_user.platform_admin):
        flash("You don't have permission to delete this service", "error")
        return redirect(url_for(".organization_dashboard", org_id=org_id))

    confirm = request.form.get("confirm_delete")
    if confirm != "delete":
        flash("Delete confirmation was not provided", "error")
        return redirect(url_for(".organization_dashboard", org_id=org_id))

    cached_service_user_ids = [user.id for user in service.active_users]

    service_api_client.archive_service(service_id, cached_service_user_ids)
    create_archive_service_event(service_id=service_id, archived_by_id=current_user.id)

    cache.redis_client.delete("organizations")

    flash(f"'{service.name}' was deleted", "default_with_tick")
    return redirect(url_for(".organization_dashboard", org_id=org_id))


def get_services_dashboard_data(organization, year):
    try:
        dashboard_data = organizations_client.get_organization_dashboard(
            organization.id, year
        )
        services = dashboard_data.get("services", [])
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard data: {e}")
        return []

    for service in services:
        service["id"] = service.get("service_id")
        service["name"] = service.get("service_name")
        service["recent_template"] = service.get("recent_sms_template_name") or "N/A"
        service["primary_contact"] = service.get("primary_contact") or "N/A"

        emails_sent = service.get("emails_sent", 0)
        sms_sent = service.get("sms_billable_units", 0)
        sms_remainder = service.get("sms_remainder", 0)
        sms_cost = service.get("sms_cost", 0)

        usage_parts = []
        if emails_sent > 0:
            usage_parts.append(f"{emails_sent:,} emails")
        if sms_sent > 0 or sms_remainder > 0:
            if sms_cost > 0:
                usage_parts.append(
                    f"{sms_sent:,} sms ({sms_remainder:,} remaining, ${sms_cost:,.2f})"
                )
            else:
                usage_parts.append(f"{sms_sent:,} sms ({sms_remainder:,} remaining)")

        service["usage"] = ", ".join(usage_parts) if usage_parts else "No usage"

    return services


@main.route("/organizations/<uuid:org_id>", methods=["GET", "POST"])
@user_has_permissions()
def organization_dashboard(org_id):
    if not current_app.config.get("ORGANIZATION_DASHBOARD_ENABLED", False):
        return redirect(url_for(".organization_usage", org_id=org_id))

    year = requested_and_current_financial_year(request)[0]
    action = request.args.get("action")
    service_id = request.args.get("service_id")

    create_service_form = None
    invite_user_form = None
    edit_service_data = None

    if action == "create-service":
        result = _handle_create_service(org_id)
        if isinstance(result, Response):
            return result
        create_service_form = result

    elif action == "invite-user":
        result = _handle_invite_user(org_id)
        if isinstance(result, Response):
            return result
        invite_user_form = result

    elif action == "edit-service" and service_id:
        result = _handle_edit_service(org_id, service_id)
        if isinstance(result, Response):
            return result
        edit_service_data = result

    elif action == "delete-service" and service_id:
        return _handle_delete_service(org_id, service_id)

    message_allowance = get_organization_message_allowance(org_id)

    return render_template(
        "views/organizations/organization/index.html",
        selected_year=year,
        services=get_services_dashboard_data(current_organization, year),
        live_services=len(current_organization.live_services),
        trial_services=len(current_organization.trial_services),
        suspended_services=len(current_organization.suspended_services),
        total_services=len(current_organization.services),
        create_service_form=create_service_form,
        invite_user_form=invite_user_form,
        edit_service_data=edit_service_data,
        new_service_id=session.pop("new_service_id", None),
        updated_service_id=session.pop("updated_service_id", None),
        **message_allowance,
    )


@main.route("/organizations/<uuid:org_id>/usage", methods=["GET"])
@user_has_permissions()
def organization_usage(org_id):
    year, current_financial_year = requested_and_current_financial_year(request)
    services = current_organization.services_and_usage(financial_year=year)["services"]

    return render_template(
        "views/organizations/organization/usage.html",
        services=services,
        years=get_tuples_of_financial_years(
            partial(url_for, ".organization_usage", org_id=current_organization.id),
            start=current_financial_year - 2,
            end=current_financial_year,
        ),
        selected_year=year,
        search_form=SearchByNameForm() if len(services) > 7 else None,
        **{
            f"total_{key}": sum(service[key] for service in services)
            for key in ("emails_sent", "sms_cost")
        },
        download_link=url_for(
            ".download_organization_usage_report", org_id=org_id, selected_year=year
        ),
    )


@main.route("/organizations/<uuid:org_id>/download-usage-report.csv", methods=["GET"])
@user_has_permissions()
def download_organization_usage_report(org_id):
    # Validate and sanitize selected_year to prevent header injection
    selected_year_input = request.args.get("selected_year", "")
    if selected_year_input.isdigit() and len(selected_year_input) == 4:
        selected_year = str(int(selected_year_input))
    else:
        selected_year = str(datetime.now().year)
    services_usage = current_organization.services_and_usage(
        financial_year=selected_year
    )["services"]

    unit_column_names = OrderedDict(
        [
            ("service_id", "Service ID"),
            ("service_name", "Service Name"),
            ("emails_sent", "Emails sent"),
            ("sms_remainder", "Free text message allowance remaining"),
        ]
    )

    monetary_column_names = OrderedDict(
        [
            ("sms_cost", "Spent on text messages ($)"),
        ]
    )

    org_usage_data = [
        list(unit_column_names.values()) + list(monetary_column_names.values())
    ] + [
        [service[attribute] for attribute in unit_column_names.keys()]
        + [
            "{:,.2f}".format(service[attribute])
            for attribute in monetary_column_names.keys()
        ]
        for service in services_usage
    ]

    # Sanitize organization name for filename to prevent header injection
    safe_org_name = re.sub(r"[^\w\s-]", "", current_organization.name).strip()
    safe_org_name = re.sub(r"[-\s]+", "-", safe_org_name)

    return (
        Spreadsheet.from_rows(org_usage_data).as_csv_data,
        200,
        {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": (
                f'inline;filename="{safe_org_name} organization usage report for year {selected_year}'
                f' - generated on {datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")}.csv"'
            ),
        },
    )


@main.route("/organizations/<uuid:org_id>/trial-services", methods=["GET"])
@user_is_platform_admin
def organization_trial_mode_services(org_id):
    return render_template(
        "views/organizations/organization/trial-mode-services.html",
        search_form=SearchByNameForm(),
    )


@main.route("/organizations/<uuid:org_id>/users", methods=["GET"])
@user_has_permissions()
def manage_org_users(org_id):
    return render_template(
        "views/organizations/organization/users/index.html",
        users=current_organization.team_members,
        show_search_box=(len(current_organization.team_members) > 7),
        form=SearchUsersForm(),
    )


@main.route("/organizations/<uuid:org_id>/users/invite", methods=["GET", "POST"])
@user_has_permissions()
def invite_org_user(org_id):
    form = InviteOrgUserForm(inviter_email_address=current_user.email_address)
    if form.validate_on_submit():
        email_address = form.email_address.data
        invited_org_user = InvitedOrgUser.create(current_user.id, org_id, email_address)

        flash(
            "Invite sent to {}".format(invited_org_user.email_address),
            "default_with_tick",
        )
        return redirect(url_for(".manage_org_users", org_id=org_id))

    return render_template(
        "views/organizations/organization/users/invite-org-user.html", form=form
    )


@main.route("/organizations/<uuid:org_id>/users/<uuid:user_id>", methods=["GET"])
@user_has_permissions()
def edit_organization_user(org_id, user_id):
    # The only action that can be done to an org user is to remove them from the org.
    # This endpoint is used to get the ID of the user to delete without passing it as a
    # query string, but it uses the template for all org team members in order to avoid
    # having a page containing a single link.
    return render_template(
        "views/organizations/organization/users/index.html",
        users=current_organization.team_members,
        show_search_box=(len(current_organization.team_members) > 7),
        form=SearchUsersForm(),
        user_to_remove=User.from_id(user_id),
    )


@main.route(
    "/organizations/<uuid:org_id>/users/<uuid:user_id>/delete", methods=["POST"]
)
@user_has_permissions()
def remove_user_from_organization(org_id, user_id):
    organizations_client.remove_user_from_organization(org_id, user_id)

    return redirect(url_for(".show_accounts_or_dashboard"))


@main.route(
    "/organizations/<uuid:org_id>/cancel-invited-user/<uuid:invited_user_id>",
    methods=["GET"],
)
@user_has_permissions()
def cancel_invited_org_user(org_id, invited_user_id):
    org_invite_api_client.cancel_invited_user(
        org_id=org_id, invited_user_id=invited_user_id
    )

    invited_org_user = InvitedOrgUser.by_id_and_org_id(org_id, invited_user_id)

    flash(
        f"Invitation cancelled for {invited_org_user.email_address}",
        "default_with_tick",
    )
    return redirect(url_for("main.manage_org_users", org_id=org_id))


@main.route("/organizations/<uuid:org_id>/settings/", methods=["GET"])
@user_is_platform_admin
def organization_settings(org_id):
    return render_template(
        "views/organizations/organization/settings/index.html",
    )


@main.route("/organizations/<uuid:org_id>/settings/edit-name", methods=["GET", "POST"])
@user_is_platform_admin
def edit_organization_name(org_id):
    form = RenameOrganizationForm(name=current_organization.name)

    if form.validate_on_submit():
        try:
            current_organization.update(name=form.name.data)
        except HTTPError as http_error:
            error_msg = "Organization name already exists"
            if http_error.status_code == 400 and error_msg in http_error.message:
                form.name.errors.append("This organization name is already in use")
            else:
                raise http_error
        else:
            return redirect(url_for(".organization_settings", org_id=org_id))

    return render_template(
        "views/organizations/organization/settings/edit-name.html",
        form=form,
    )


@main.route("/organizations/<uuid:org_id>/settings/edit-type", methods=["GET", "POST"])
@user_is_platform_admin
def edit_organization_type(org_id):
    form = OrganizationOrganizationTypeForm(
        organization_type=current_organization.organization_type
    )

    if form.validate_on_submit():
        current_organization.update(
            organization_type=form.organization_type.data,
            delete_services_cache=True,
        )
        return redirect(url_for(".organization_settings", org_id=org_id))

    return render_template(
        "views/organizations/organization/settings/edit-type.html",
        form=form,
    )


@main.route(
    "/organizations/<uuid:org_id>/settings/edit-organization-domains",
    methods=["GET", "POST"],
)
@user_is_platform_admin
def edit_organization_domains(org_id):
    form = AdminOrganizationDomainsForm()

    if form.validate_on_submit():
        try:
            organizations_client.update_organization(
                org_id,
                domains=list(
                    OrderedDict.fromkeys(
                        domain.lower() for domain in filter(None, form.domains.data)
                    )
                ),
            )
        except HTTPError as e:
            error_message = "Domain already exists"
            if e.status_code == 400 and error_message in e.message:
                flash("This domain is already in use", "error")
                return render_template(
                    "views/organizations/organization/settings/edit-domains.html",
                    form=form,
                )
            else:
                raise e
        return redirect(url_for(".organization_settings", org_id=org_id))

    form.populate(current_organization.domains)

    return render_template(
        "views/organizations/organization/settings/edit-domains.html",
        form=form,
    )


@main.route("/organizations/<uuid:org_id>/settings/notes", methods=["GET", "POST"])
@user_is_platform_admin
def edit_organization_notes(org_id):
    form = AdminNotesForm(notes=current_organization.notes)

    if form.validate_on_submit():
        if form.notes.data == current_organization.notes:
            return redirect(url_for(".organization_settings", org_id=org_id))

        current_organization.update(notes=form.notes.data)
        return redirect(url_for(".organization_settings", org_id=org_id))

    return render_template(
        "views/organizations/organization/settings/edit-organization-notes.html",
        form=form,
    )


@main.route(
    "/organizations/<uuid:org_id>/settings/edit-billing-details",
    methods=["GET", "POST"],
)
@user_is_platform_admin
def edit_organization_billing_details(org_id):
    form = AdminBillingDetailsForm(
        billing_contact_email_addresses=current_organization.billing_contact_email_addresses,
        billing_contact_names=current_organization.billing_contact_names,
        billing_reference=current_organization.billing_reference,
        purchase_order_number=current_organization.purchase_order_number,
        notes=current_organization.notes,
    )

    if form.validate_on_submit():
        current_organization.update(
            billing_contact_email_addresses=form.billing_contact_email_addresses.data,
            billing_contact_names=form.billing_contact_names.data,
            billing_reference=form.billing_reference.data,
            purchase_order_number=form.purchase_order_number.data,
            notes=form.notes.data,
        )
        return redirect(url_for(".organization_settings", org_id=org_id))

    return render_template(
        "views/organizations/organization/settings/edit-organization-billing-details.html",
        form=form,
    )


@main.route("/organizations/<uuid:org_id>/billing")
@user_is_platform_admin
def organization_billing(org_id):
    return render_template("views/organizations/organization/billing.html")
