from collections import OrderedDict
from datetime import datetime
from functools import partial

from flask import flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user
from notifications_python_client.errors import HTTPError

from app import (
    current_organisation,
    email_branding_client,
    org_invite_api_client,
    organisations_client,
)
from app.main import main
from app.main.forms import (
    AdminBillingDetailsForm,
    AdminNewOrganisationForm,
    AdminNotesForm,
    AdminOrganisationDomainsForm,
    AdminOrganisationGoLiveNotesForm,
    AdminPreviewBrandingForm,
    AdminSetEmailBrandingForm,
    InviteOrgUserForm,
    OrganisationAgreementSignedForm,
    OrganisationCrownStatusForm,
    OrganisationOrganisationTypeForm,
    RenameOrganisationForm,
    SearchByNameForm,
    SearchUsersForm,
)
from app.main.views.dashboard import (
    get_tuples_of_financial_years,
    requested_and_current_financial_year,
)
from app.main.views.service_settings import get_branding_as_value_and_label
from app.models.organisation import AllOrganisations, Organisation
from app.models.user import InvitedOrgUser, User
from app.s3_client.s3_mou_client import get_mou
from app.utils.csv import Spreadsheet
from app.utils.user import user_has_permissions, user_is_platform_admin


@main.route("/organisations", methods=['GET'])
@user_is_platform_admin
def organisations():
    return render_template(
        'views/organisations/index.html',
        organisations=AllOrganisations(),
        search_form=SearchByNameForm(),
    )


@main.route("/organisations/add", methods=['GET', 'POST'])
@user_is_platform_admin
def add_organisation():
    form = AdminNewOrganisationForm()

    if form.validate_on_submit():
        try:
            return redirect(url_for(
                '.organisation_settings',
                org_id=Organisation.create_from_form(form).id,
            ))
        except HTTPError as e:
            msg = 'Organisation name already exists'
            if e.status_code == 400 and msg in e.message:
                form.name.errors.append("This organisation name is already in use")
            else:
                raise e

    return render_template(
        'views/organisations/add-organisation.html',
        form=form
    )


@main.route("/organisations/<uuid:org_id>", methods=['GET'])
@user_has_permissions()
def organisation_dashboard(org_id):
    year, current_financial_year = requested_and_current_financial_year(request)
    services = current_organisation.services_and_usage(
        financial_year=year
    )['services']
    return render_template(
        'views/organisations/organisation/index.html',
        services=services,
        years=get_tuples_of_financial_years(
            partial(url_for, '.organisation_dashboard', org_id=current_organisation.id),
            start=current_financial_year - 2,
            end=current_financial_year,
        ),
        selected_year=year,
        search_form=SearchByNameForm() if len(services) > 7 else None,
        **{
            f'total_{key}': sum(service[key] for service in services)
            for key in ('emails_sent', 'sms_cost')
        },
        download_link=url_for(
            '.download_organisation_usage_report',
            org_id=org_id,
            selected_year=year
        )
    )


@main.route("/organisations/<uuid:org_id>/download-usage-report.csv", methods=['GET'])
@user_has_permissions()
def download_organisation_usage_report(org_id):
    selected_year = request.args.get('selected_year')
    services_usage = current_organisation.services_and_usage(
        financial_year=selected_year
    )['services']

    unit_column_names = OrderedDict([
        ('service_id', 'Service ID'),
        ('service_name', 'Service Name'),
        ('emails_sent', 'Emails sent'),
        ('sms_remainder', 'Free text message allowance remaining'),
    ])

    monetary_column_names = OrderedDict([
        ('sms_cost', 'Spent on text messages ($)'),
    ])

    org_usage_data = [
        list(unit_column_names.values()) + list(monetary_column_names.values())
    ] + [
        [
            service[attribute] for attribute in unit_column_names.keys()
        ] + [
            '{:,.2f}'.format(service[attribute]) for attribute in monetary_column_names.keys()
        ]
        for service in services_usage
    ]

    return Spreadsheet.from_rows(org_usage_data).as_csv_data, 200, {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': (
            'inline;'
            'filename="{} organisation usage report for year {}'
            ' - generated on {}.csv"'.format(
                current_organisation.name,
                selected_year,
                datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            ))
    }


@main.route("/organisations/<uuid:org_id>/trial-services", methods=['GET'])
@user_is_platform_admin
def organisation_trial_mode_services(org_id):
    return render_template(
        'views/organisations/organisation/trial-mode-services.html',
        search_form=SearchByNameForm(),
    )


@main.route("/organisations/<uuid:org_id>/users", methods=['GET'])
@user_has_permissions()
def manage_org_users(org_id):
    return render_template(
        'views/organisations/organisation/users/index.html',
        users=current_organisation.team_members,
        show_search_box=(len(current_organisation.team_members) > 7),
        form=SearchUsersForm(),
    )


@main.route("/organisations/<uuid:org_id>/users/invite", methods=['GET', 'POST'])
@user_has_permissions()
def invite_org_user(org_id):
    form = InviteOrgUserForm(
        inviter_email_address=current_user.email_address
    )
    if form.validate_on_submit():
        email_address = form.email_address.data
        invited_org_user = InvitedOrgUser.create(
            current_user.id,
            org_id,
            email_address
        )

        flash('Invite sent to {}'.format(invited_org_user.email_address), 'default_with_tick')
        return redirect(url_for('.manage_org_users', org_id=org_id))

    return render_template(
        'views/organisations/organisation/users/invite-org-user.html',
        form=form
    )


@main.route("/organisations/<uuid:org_id>/users/<uuid:user_id>", methods=['GET'])
@user_has_permissions()
def edit_organisation_user(org_id, user_id):
    # The only action that can be done to an org user is to remove them from the org.
    # This endpoint is used to get the ID of the user to delete without passing it as a
    # query string, but it uses the template for all org team members in order to avoid
    # having a page containing a single link.
    return render_template(
        'views/organisations/organisation/users/index.html',
        users=current_organisation.team_members,
        show_search_box=(len(current_organisation.team_members) > 7),
        form=SearchUsersForm(),
        user_to_remove=User.from_id(user_id)
    )


@main.route("/organisations/<uuid:org_id>/users/<uuid:user_id>/delete", methods=['POST'])
@user_has_permissions()
def remove_user_from_organisation(org_id, user_id):
    organisations_client.remove_user_from_organisation(org_id, user_id)

    return redirect(url_for('.show_accounts_or_dashboard'))


@main.route("/organisations/<uuid:org_id>/cancel-invited-user/<uuid:invited_user_id>", methods=['GET'])
@user_has_permissions()
def cancel_invited_org_user(org_id, invited_user_id):
    org_invite_api_client.cancel_invited_user(org_id=org_id, invited_user_id=invited_user_id)

    invited_org_user = InvitedOrgUser.by_id_and_org_id(org_id, invited_user_id)

    flash(f'Invitation cancelled for {invited_org_user.email_address}', 'default_with_tick')
    return redirect(url_for('main.manage_org_users', org_id=org_id))


@main.route("/organisations/<uuid:org_id>/settings/", methods=['GET'])
@user_is_platform_admin
def organisation_settings(org_id):
    return render_template(
        'views/organisations/organisation/settings/index.html',
    )


@main.route("/organisations/<uuid:org_id>/settings/edit-name", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_organisation_name(org_id):
    form = RenameOrganisationForm(name=current_organisation.name)

    if form.validate_on_submit():

        try:
            current_organisation.update(name=form.name.data)
        except HTTPError as http_error:
            error_msg = 'Organisation name already exists'
            if http_error.status_code == 400 and error_msg in http_error.message:
                form.name.errors.append('This organisation name is already in use')
            else:
                raise http_error
        else:
            return redirect(url_for('.organisation_settings', org_id=org_id))

    return render_template(
        'views/organisations/organisation/settings/edit-name.html',
        form=form,
    )


@main.route("/organisations/<uuid:org_id>/settings/edit-type", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_organisation_type(org_id):

    form = OrganisationOrganisationTypeForm(
        organisation_type=current_organisation.organisation_type
    )

    if form.validate_on_submit():
        current_organisation.update(
            organisation_type=form.organisation_type.data,
            delete_services_cache=True,
        )
        return redirect(url_for('.organisation_settings', org_id=org_id))

    return render_template(
        'views/organisations/organisation/settings/edit-type.html',
        form=form,
    )


@main.route("/organisations/<uuid:org_id>/settings/edit-crown-status", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_organisation_crown_status(org_id):

    form = OrganisationCrownStatusForm(
        crown_status={
            True: 'crown',
            False: 'non-crown',
            None: 'unknown',
        }.get(current_organisation.crown)
    )

    if form.validate_on_submit():
        organisations_client.update_organisation(
            current_organisation.id,
            crown={
                'crown': True,
                'non-crown': False,
                'unknown': None,
            }.get(form.crown_status.data),
        )
        return redirect(url_for('.organisation_settings', org_id=org_id))

    return render_template(
        'views/organisations/organisation/settings/edit-crown-status.html',
        form=form,
    )


@main.route("/organisations/<uuid:org_id>/settings/edit-agreement", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_organisation_agreement(org_id):

    form = OrganisationAgreementSignedForm(
        agreement_signed={
            True: 'yes',
            False: 'no',
            None: 'unknown',
        }.get(current_organisation.agreement_signed)
    )

    if form.validate_on_submit():
        organisations_client.update_organisation(
            current_organisation.id,
            agreement_signed={
                'yes': True,
                'no': False,
                'unknown': None,
            }.get(form.agreement_signed.data),
        )
        return redirect(url_for('.organisation_settings', org_id=org_id))

    return render_template(
        'views/organisations/organisation/settings/edit-agreement.html',
        form=form,
    )


@main.route("/organisations/<uuid:org_id>/settings/set-email-branding", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_organisation_email_branding(org_id):

    email_branding = email_branding_client.get_all_email_branding()

    form = AdminSetEmailBrandingForm(
        all_branding_options=get_branding_as_value_and_label(email_branding),
        current_branding=current_organisation.email_branding_id,
    )

    if form.validate_on_submit():
        return redirect(url_for(
            '.organisation_preview_email_branding',
            org_id=org_id,
            branding_style=form.branding_style.data,
        ))

    return render_template(
        'views/organisations/organisation/settings/set-email-branding.html',
        form=form,
        search_form=SearchByNameForm()
    )


@main.route("/organisations/<uuid:org_id>/settings/preview-email-branding", methods=['GET', 'POST'])
@user_is_platform_admin
def organisation_preview_email_branding(org_id):

    branding_style = request.args.get('branding_style', None)

    form = AdminPreviewBrandingForm(branding_style=branding_style)

    if form.validate_on_submit():
        current_organisation.update(
            email_branding_id=form.branding_style.data,
            delete_services_cache=True,
        )
        return redirect(url_for('.organisation_settings', org_id=org_id))

    return render_template(
        'views/organisations/organisation/settings/preview-email-branding.html',
        form=form,
        action=url_for('main.organisation_preview_email_branding', org_id=org_id),
    )


@main.route("/organisations/<uuid:org_id>/settings/edit-organisation-domains", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_organisation_domains(org_id):

    form = AdminOrganisationDomainsForm()

    if form.validate_on_submit():
        try:
            organisations_client.update_organisation(
                org_id,
                domains=list(OrderedDict.fromkeys(
                    domain.lower()
                    for domain in filter(None, form.domains.data)
                )),
            )
        except HTTPError as e:
            error_message = "Domain already exists"
            if e.status_code == 400 and error_message in e.message:
                flash("This domain is already in use", "error")
                return render_template(
                    'views/organisations/organisation/settings/edit-domains.html',
                    form=form,
                )
            else:
                raise e
        return redirect(url_for('.organisation_settings', org_id=org_id))

    form.populate(current_organisation.domains)

    return render_template(
        'views/organisations/organisation/settings/edit-domains.html',
        form=form,
    )


@main.route("/organisations/<uuid:org_id>/settings/edit-go-live-notes", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_organisation_go_live_notes(org_id):

    form = AdminOrganisationGoLiveNotesForm()

    if form.validate_on_submit():
        organisations_client.update_organisation(
            org_id,
            request_to_go_live_notes=form.request_to_go_live_notes.data
        )
        return redirect(url_for('.organisation_settings', org_id=org_id))

    org = organisations_client.get_organisation(org_id)
    form.request_to_go_live_notes.data = org['request_to_go_live_notes']

    return render_template(
        'views/organisations/organisation/settings/edit-go-live-notes.html',
        form=form,
    )


@main.route("/organisations/<uuid:org_id>/settings/notes", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_organisation_notes(org_id):
    form = AdminNotesForm(notes=current_organisation.notes)

    if form.validate_on_submit():

        if form.notes.data == current_organisation.notes:
            return redirect(url_for('.organisation_settings', org_id=org_id))

        current_organisation.update(
            notes=form.notes.data
        )
        return redirect(url_for('.organisation_settings', org_id=org_id))

    return render_template(
        'views/organisations/organisation/settings/edit-organisation-notes.html',
        form=form,
    )


@main.route("/organisations/<uuid:org_id>/settings/edit-billing-details", methods=['GET', 'POST'])
@user_is_platform_admin
def edit_organisation_billing_details(org_id):
    form = AdminBillingDetailsForm(
        billing_contact_email_addresses=current_organisation.billing_contact_email_addresses,
        billing_contact_names=current_organisation.billing_contact_names,
        billing_reference=current_organisation.billing_reference,
        purchase_order_number=current_organisation.purchase_order_number,
        notes=current_organisation.notes,
    )

    if form.validate_on_submit():
        current_organisation.update(
            billing_contact_email_addresses=form.billing_contact_email_addresses.data,
            billing_contact_names=form.billing_contact_names.data,
            billing_reference=form.billing_reference.data,
            purchase_order_number=form.purchase_order_number.data,
            notes=form.notes.data,
        )
        return redirect(url_for('.organisation_settings', org_id=org_id))

    return render_template(
        'views/organisations/organisation/settings/edit-organisation-billing-details.html',
        form=form,
    )


@main.route("/organisations/<uuid:org_id>/billing")
@user_is_platform_admin
def organisation_billing(org_id):
    return render_template(
        'views/organisations/organisation/billing.html'
    )


@main.route('/organisations/<uuid:org_id>/agreement.pdf')
@user_is_platform_admin
def organisation_download_agreement(org_id):
    return send_file(**get_mou(
        current_organisation.crown_status_or_404
    ))
