# -*- coding: utf-8 -*-

from flask import (
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    stream_with_context,
    url_for,
)
from flask_login import current_user
from notifications_python_client.errors import HTTPError
from notifications_utils.template import Template, WithSubjectTemplate

from app import (
    current_service,
    format_datetime_short,
    format_thousands,
    notification_api_client,
    service_api_client,
)
from app.main import main
from app.main.forms import SearchNotificationsForm
from app.models.job import Job
from app.utils import (
    generate_next_dict,
    generate_notifications_csv,
    generate_previous_dict,
    get_letter_printing_statement,
    get_page_from_request,
    get_time_left,
    parse_filter_args,
    printing_today_or_tomorrow,
    set_status_filters,
    user_has_permissions,
)


@main.route("/services/<uuid:service_id>/jobs")
@user_has_permissions()
def view_jobs(service_id):
    jobs = current_service.get_page_of_jobs(page=request.args.get('page'))

    prev_page = None
    if jobs.prev_page:
        prev_page = generate_previous_dict('main.view_jobs', service_id, jobs.current_page)
    next_page = None
    if jobs.next_page:
        next_page = generate_next_dict('main.view_jobs', service_id, jobs.current_page)

    return render_template(
        'views/jobs/jobs.html',
        jobs=jobs,
        prev_page=prev_page,
        next_page=next_page,
        show_scheduled_jobs=(
            jobs.current_page == 1
            and not current_user.has_permissions('view_activity')
            and current_service.scheduled_jobs
        ),
    )


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>")
@user_has_permissions()
def view_job(service_id, job_id):
    job = Job.from_id(job_id, service_id=current_service.id)
    if job.cancelled:
        abort(404)

    filter_args = parse_filter_args(request.args)
    filter_args['status'] = set_status_filters(filter_args)

    just_sent_message = 'Your {} been sent. Printing starts {} at 5:30pm.'.format(
        'letter has' if job.notification_count == 1 else 'letters have',
        printing_today_or_tomorrow()
    )

    return render_template(
        'views/jobs/job.html',
        job=job,
        status=request.args.get('status', ''),
        updates_url=url_for(
            ".view_job_updates",
            service_id=service_id,
            job_id=job.id,
            status=request.args.get('status', ''),
        ),
        partials=get_job_partials(job),
        just_sent=bool(
            request.args.get('just_sent') == 'yes'
            and job.template_type == 'letter'
        ),
        just_sent_message=just_sent_message,
    )


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>.csv")
@user_has_permissions('view_activity')
def view_job_csv(service_id, job_id):
    job = Job.from_id(job_id, service_id=service_id)
    filter_args = parse_filter_args(request.args)
    filter_args['status'] = set_status_filters(filter_args)

    return Response(
        stream_with_context(
            generate_notifications_csv(
                service_id=service_id,
                job_id=job_id,
                status=filter_args.get('status'),
                page=request.args.get('page', 1),
                page_size=5000,
                format_for_csv=True,
                template_type=job.template_type,
            )
        ),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'inline; filename="{} - {}.csv"'.format(
                job.template['name'],
                format_datetime_short(job.created_at)
            )
        }
    )


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>", methods=['POST'])
@user_has_permissions('send_messages')
def cancel_job(service_id, job_id):
    Job.from_id(job_id, service_id=service_id).cancel()
    return redirect(url_for('main.service_dashboard', service_id=service_id))


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>/cancel", methods=['GET', 'POST'])
@user_has_permissions()
def cancel_letter_job(service_id, job_id):
    if request.method == 'POST':
        job = Job.from_id(job_id, service_id=service_id)

        if job.status != 'finished' or job.notifications_created < job.notification_count:
            flash("We are still processing these letters, please try again in a minute.", 'try again')
            return view_job(service_id, job_id)
        try:
            number_of_letters = job.cancel()
        except HTTPError as e:
            flash(e.message, 'dangerous')
            return redirect(url_for('main.view_job', service_id=service_id, job_id=job_id))
        flash("Cancelled {} letters from {}".format(
            format_thousands(number_of_letters), job.original_file_name
        ), 'default_with_tick')
        return redirect(url_for('main.service_dashboard', service_id=service_id))

    flash("Are you sure you want to cancel sending these letters?", 'cancel')
    return view_job(service_id, job_id)


@main.route("/services/<uuid:service_id>/jobs/<uuid:job_id>.json")
@user_has_permissions()
def view_job_updates(service_id, job_id):

    job = Job.from_id(job_id, service_id=service_id)

    return jsonify(**get_job_partials(job))


@main.route('/services/<uuid:service_id>/notifications', methods=['GET', 'POST'])
@main.route('/services/<uuid:service_id>/notifications/<template_type:message_type>', methods=['GET', 'POST'])
@user_has_permissions()
def view_notifications(service_id, message_type=None):
    return render_template(
        'views/notifications.html',
        partials=get_notifications(service_id, message_type),
        message_type=message_type,
        status=request.args.get('status') or 'sending,delivered,failed',
        page=request.args.get('page', 1),
        to=request.form.get('to', ''),
        search_form=SearchNotificationsForm(
            message_type=message_type,
            to=request.form.get('to', ''),
        ),
        things_you_can_search_by={
            'email': ['email address'],
            'sms': ['phone number'],
            'letter': [],
            None: ['email address', 'phone number'],
        }.get(message_type) + {
            True: ['reference'],
            False: [],
        }.get(bool(current_service.api_keys)),
        download_link=url_for(
            '.download_notifications_csv',
            service_id=current_service.id,
            message_type=message_type,
            status=request.args.get('status')
        )
    )


@main.route('/services/<uuid:service_id>/notifications.json', methods=['GET', 'POST'])
@main.route('/services/<uuid:service_id>/notifications/<template_type:message_type>.json', methods=['GET', 'POST'])
@user_has_permissions()
def get_notifications_as_json(service_id, message_type=None):
    return jsonify(get_notifications(
        service_id, message_type, status_override=request.args.get('status')
    ))


@main.route('/services/<uuid:service_id>/notifications.csv', endpoint="view_notifications_csv")
@main.route(
    '/services/<uuid:service_id>/notifications/<template_type:message_type>.csv',
    endpoint="view_notifications_csv"
)
@user_has_permissions()
def get_notifications(service_id, message_type, status_override=None):
    # TODO get the api to return count of pages as well.
    page = get_page_from_request()
    if page is None:
        abort(404, "Invalid page argument ({}).".format(request.args.get('page')))
    filter_args = parse_filter_args(request.args)
    filter_args['status'] = set_status_filters(filter_args)
    service_data_retention_days = None

    if message_type is not None:
        service_data_retention_days = current_service.get_days_of_retention(message_type)

    if request.path.endswith('csv') and current_user.has_permissions('view_activity'):
        return Response(
            generate_notifications_csv(
                service_id=service_id,
                page=page,
                page_size=5000,
                template_type=[message_type],
                status=filter_args.get('status'),
                limit_days=service_data_retention_days
            ),
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'inline; filename="notifications.csv"'}
        )
    notifications = notification_api_client.get_notifications_for_service(
        service_id=service_id,
        page=page,
        template_type=[message_type] if message_type else [],
        status=filter_args.get('status'),
        limit_days=service_data_retention_days,
        to=request.form.get('to', ''),
    )
    url_args = {
        'message_type': message_type,
        'status': request.args.get('status')
    }
    prev_page = None

    if 'links' in notifications and notifications['links'].get('prev', None):
        prev_page = generate_previous_dict('main.view_notifications', service_id, page, url_args=url_args)
    next_page = None

    if 'links' in notifications and notifications['links'].get('next', None):
        next_page = generate_next_dict('main.view_notifications', service_id, page, url_args)

    if message_type:
        download_link = url_for(
            '.view_notifications_csv',
            service_id=current_service.id,
            message_type=message_type,
            status=request.args.get('status')
        )
    else:
        download_link = None

    return {
        'service_data_retention_days': service_data_retention_days,
        'counts': render_template(
            'views/activity/counts.html',
            status=request.args.get('status'),
            status_filters=get_status_filters(
                current_service,
                message_type,
                service_api_client.get_service_statistics(
                    service_id,
                    today_only=False,
                    limit_days=service_data_retention_days
                )
            )
        ),
        'notifications': render_template(
            'views/activity/notifications.html',
            notifications=list(add_preview_of_content_to_notifications(
                notifications['notifications']
            )),
            page=page,
            limit_days=service_data_retention_days,
            prev_page=prev_page,
            next_page=next_page,
            status=request.args.get('status'),
            message_type=message_type,
            download_link=download_link,
        ),
    }


def get_status_filters(service, message_type, statistics):
    if message_type is None:
        stats = {
            key: sum(
                statistics[message_type][key]
                for message_type in {'email', 'sms', 'letter'}
            )
            for key in {'requested', 'delivered', 'failed'}
        }
    else:
        stats = statistics[message_type]
    stats['sending'] = stats['requested'] - stats['delivered'] - stats['failed']

    filters = [
        # key, label, option
        ('requested', 'total', 'sending,delivered,failed'),
        ('sending', 'sending', 'sending'),
        ('delivered', 'delivered', 'delivered'),
        ('failed', 'failed', 'failed'),
    ]
    return [
        # return list containing label, option, link, count
        (
            label,
            option,
            url_for(
                '.view_notifications',
                service_id=service.id,
                message_type=message_type,
                status=option
            ),
            stats[key]
        )
        for key, label, option in filters
    ]


def _get_job_counts(job):
    return [
        (
            label,
            query_param,
            url_for(
                ".view_job",
                service_id=job.service,
                job_id=job.id,
                status=query_param,
            ),
            count
        ) for label, query_param, count in [
            [
                'total', '',
                job.notification_count
            ],
            [
                'sending', 'sending',
                job.notifications_sending
            ],
            [
                'delivered', 'delivered',
                job.notifications_delivered
            ],
            [
                'failed', 'failed',
                job.notifications_failed
            ]
        ]
    ]


def get_job_partials(job):
    filter_args = parse_filter_args(request.args)
    filter_args['status'] = set_status_filters(filter_args)
    notifications = job.get_notifications(status=filter_args['status'])
    if job.template_type == 'letter':
        counts = render_template(
            'partials/jobs/count-letters.html',
            job=job,
        )
    else:
        counts = render_template(
            'partials/count.html',
            counts=_get_job_counts(job),
            status=filter_args['status'],
            notifications_deleted=(
                job.status == 'finished' and not notifications['notifications']
            ),
        )
    service_data_retention_days = current_service.get_days_of_retention(job.template_type)

    return {
        'counts': counts,
        'notifications': render_template(
            'partials/jobs/notifications.html',
            notifications=list(
                add_preview_of_content_to_notifications(notifications['notifications'])
            ),
            more_than_one_page=bool(notifications.get('links', {}).get('next')),
            download_link=url_for(
                '.view_job_csv',
                service_id=current_service.id,
                job_id=job.id,
                status=request.args.get('status')
            ),
            time_left=get_time_left(job.created_at, service_data_retention_days=service_data_retention_days),
            job=job,
            service_data_retention_days=service_data_retention_days,
        ),
        'status': render_template(
            'partials/jobs/status.html',
            job=job,
            letter_print_day=get_letter_printing_statement("created", job.created_at)
        ),
    }


def add_preview_of_content_to_notifications(notifications):

    for notification in notifications:

        if notification['template'].get('redact_personalisation'):
            notification['personalisation'] = {}

        if notification['template']['template_type'] == 'sms':
            yield dict(
                preview_of_content=str(Template(
                    notification['template'],
                    notification['personalisation'],
                    redact_missing_personalisation=True,
                )),
                **notification
            )
        else:
            if notification['template']['is_precompiled_letter']:
                notification['template']['subject'] = notification['client_reference']
            yield dict(
                preview_of_content=(
                    WithSubjectTemplate(
                        notification['template'],
                        notification['personalisation'],
                        redact_missing_personalisation=True,
                    ).subject
                ),
                **notification
            )
