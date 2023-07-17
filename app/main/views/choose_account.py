from flask import redirect, render_template, session, url_for
from flask_login import current_user

from app import status_api_client
from app.main import main
from app.models.organization import AllOrganizations
from app.utils import PermanentRedirect
from app.utils.user import user_is_logged_in


@main.route("/services")
def choose_service():
    raise PermanentRedirect(url_for('.choose_account'))


@main.route("/services-or-dashboard")
def services_or_dashboard():
    raise PermanentRedirect(url_for('.show_accounts_or_dashboard'))


@main.route("/accounts")
@user_is_logged_in
def choose_account():
    org_count, live_service_count = None, None
    if current_user.platform_admin:
        org_count, live_service_count = (
            len(AllOrganizations()),
            status_api_client.get_count_of_live_services_and_organizations()['services'],
        )
    return render_template(
        'views/choose-account.html',
        can_add_service=current_user.is_gov_user,
        org_count=org_count,
        live_service_count=live_service_count,
    )


@main.route("/accounts-or-dashboard")
def show_accounts_or_dashboard():

    if not current_user.is_authenticated:
        return redirect(url_for('.index'))

    service_id = session.get('service_id')
    if service_id and (current_user.belongs_to_service(service_id) or current_user.platform_admin):
        return redirect(url_for('.service_dashboard', service_id=service_id))

    organization_id = session.get('organization_id')
    if organization_id and (current_user.belongs_to_organization(organization_id) or current_user.platform_admin):
        return redirect(url_for('.organization_dashboard', org_id=organization_id))

    if len(current_user.service_ids) == 1 and not current_user.organization_ids:
        return redirect(url_for('.service_dashboard', service_id=current_user.service_ids[0]))

    if len(current_user.organization_ids) == 1 and not current_user.trial_mode_services:
        return redirect(url_for('.organization_dashboard', org_id=current_user.organization_ids[0]))

    return redirect(url_for('.choose_account'))
