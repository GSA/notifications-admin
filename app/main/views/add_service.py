from flask import current_app, redirect, render_template, session, url_for
from flask_login import current_user
from notifications_python_client.errors import HTTPError

from app import service_api_client
from app.formatters import email_safe
from app.main import main
from app.main.forms import CreateNhsServiceForm, CreateServiceForm
from app.utils.user import user_is_gov_user, user_is_logged_in


def _create_service(service_name, organisation_type, email_from, form):

    try:
        service_id = service_api_client.create_service(
            service_name=service_name,
            organisation_type=organisation_type,
            message_limit=current_app.config['DEFAULT_SERVICE_LIMIT'],
            restricted=True,
            user_id=session['user_id'],
            email_from=email_from,
        )
        session['service_id'] = service_id

        return service_id, None
    except HTTPError as e:
        if e.status_code == 400 and e.message['name']:
            form.name.errors.append("This service name is already in use")
            return None, e
        else:
            raise e


def _create_example_template(service_id):
    example_sms_template = service_api_client.create_service_template(
        'Example text message template',
        'sms',
        'Hi, I’m trying out US Notify. Today is ((day of week)) and my favourite colour is ((colour)).',
        service_id,
    )
    return example_sms_template


@main.route("/add-service", methods=['GET', 'POST'])
@user_is_logged_in
@user_is_gov_user
def add_service():
    default_organisation_type = current_user.default_organisation_type
    if default_organisation_type == 'nhs':
        form = CreateNhsServiceForm()
        default_organisation_type = None
    else:
        form = CreateServiceForm(
            organisation_type=default_organisation_type
        )

    if form.validate_on_submit():
        email_from = email_safe(form.name.data)
        service_name = form.name.data

        service_id, error = _create_service(
            service_name,
            default_organisation_type or form.organisation_type.data,
            email_from,
            form,
        )
        if error:
            return _render_add_service_page(form, default_organisation_type)
        if len(service_api_client.get_active_services({'user_id': session['user_id']}).get('data', [])) > 1:
            return redirect(url_for('main.service_dashboard', service_id=service_id))

        example_sms_template = _create_example_template(service_id)

        return redirect(url_for(
            'main.begin_tour',
            service_id=service_id,
            template_id=example_sms_template['data']['id']
        ))
    else:
        return _render_add_service_page(form, default_organisation_type)


def _render_add_service_page(form, default_organisation_type):
    heading = 'About your service'

    if default_organisation_type == 'local':
        return render_template(
            'views/add-service-local.html',
            form=form,
            heading=heading,
            default_organisation_type=default_organisation_type,
        )

    return render_template(
        'views/add-service.html',
        form=form,
        heading=heading,
        default_organisation_type=default_organisation_type,
    )
