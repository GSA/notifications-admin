from collections import OrderedDict
from datetime import datetime
from functools import partial

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user
from notifications_python_client.errors import HTTPError

from app import (
    current_organization,
    email_branding_client,
    org_invite_api_client,
    organizations_client,
)
from app.main import main
from app.main.forms import (
    AdminBillingDetailsForm,
    AdminNewOrganizationForm,
    AdminNotesForm,
    AdminOrganizationDomainsForm,
    AdminOrganizationGoLiveNotesForm,
    AdminPreviewBrandingForm,
    AdminSetEmailBrandingForm,
    InviteOrgUserForm,
    OrganizationOrganizationTypeForm,
    RenameOrganizationForm,
    SearchByNameForm,
    SearchUsersForm,
)
from app.main.views.dashboard import (
    get_tuples_of_financial_years,
    requested_and_current_financial_year,
)
from app.main.views.service_settings import get_branding_as_value_and_label
from app.models.organization import AllOrganizations, Organization
from app.models.user import InvitedOrgUser, User
from app.utils.csv import Spreadsheet
from app.utils.user import user_has_permissions, user_is_platform_admin


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


@main.route("/organizations/<uuid:org_id>", methods=["GET"])
@user_has_permissions()
def organization_dashboard(org_id):
    year, current_financial_year = requested_and_current_financial_year(request)
    services = current_organization.services_and_usage(financial_year=year)["services"]
    return render_template(
        "views/organizations/organization/index.html",
        services=services,
        years=get_tuples_of_financial_years(
            partial(url_for, ".organization_dashboard", org_id=current_organization.id),
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
    selected_year = request.args.get("selected_year")
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

    return (
        Spreadsheet.from_rows(org_usage_data).as_csv_data,
        200,
        {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": (
                "inline;"
                'filename="{} organization usage report for year {}'
                ' - generated on {}.csv"'.format(
                    current_organization.name,
                    selected_year,
                    datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                )
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
    "/organizations/<uuid:org_id>/settings/set-email-branding", methods=["GET", "POST"]
)
@user_is_platform_admin
def edit_organization_email_branding(org_id):
    email_branding = email_branding_client.get_all_email_branding()

    form = AdminSetEmailBrandingForm(
        all_branding_options=get_branding_as_value_and_label(email_branding),
        current_branding=current_organization.email_branding_id,
    )

    if form.validate_on_submit():
        return redirect(
            url_for(
                ".organization_preview_email_branding",
                org_id=org_id,
                branding_style=form.branding_style.data,
            )
        )

    return render_template(
        "views/organizations/organization/settings/set-email-branding.html",
        form=form,
        search_form=SearchByNameForm(),
    )


@main.route(
    "/organizations/<uuid:org_id>/settings/preview-email-branding",
    methods=["GET", "POST"],
)
@user_is_platform_admin
def organization_preview_email_branding(org_id):
    branding_style = request.args.get("branding_style", None)

    form = AdminPreviewBrandingForm(branding_style=branding_style)

    if form.validate_on_submit():
        current_organization.update(
            email_branding_id=form.branding_style.data,
            delete_services_cache=True,
        )
        return redirect(url_for(".organization_settings", org_id=org_id))

    return render_template(
        "views/organizations/organization/settings/preview-email-branding.html",
        form=form,
        action=url_for("main.organization_preview_email_branding", org_id=org_id),
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


@main.route(
    "/organizations/<uuid:org_id>/settings/edit-go-live-notes", methods=["GET", "POST"]
)
@user_is_platform_admin
def edit_organization_go_live_notes(org_id):
    form = AdminOrganizationGoLiveNotesForm()

    if form.validate_on_submit():
        organizations_client.update_organization(
            org_id, request_to_go_live_notes=form.request_to_go_live_notes.data
        )
        return redirect(url_for(".organization_settings", org_id=org_id))

    org = organizations_client.get_organization(org_id)
    form.request_to_go_live_notes.data = org["request_to_go_live_notes"]

    return render_template(
        "views/organizations/organization/settings/edit-go-live-notes.html",
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
