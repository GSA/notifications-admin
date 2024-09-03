import csv
import itertools
import json
from collections import OrderedDict
from datetime import datetime
from io import StringIO

from flask import (
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from notifications_python_client.errors import HTTPError

from app import (
    billing_api_client,
    complaint_api_client,
    format_date_numeric,
    notification_api_client,
    platform_stats_api_client,
    service_api_client,
    user_api_client,
)
from app.extensions import redis_client
from app.main import main
from app.main.forms import (
    AdminClearCacheForm,
    BillingReportDateFilterForm,
    DateFilterForm,
    RequiredDateFilterForm,
)
from app.main.views.send import _send_notification
from app.statistics_utils import (
    get_formatted_percentage,
    get_formatted_percentage_two_dp,
)
from app.utils.csv import Spreadsheet
from app.utils.pagination import (
    generate_next_dict,
    generate_previous_dict,
    get_page_from_request,
)
from app.utils.user import user_is_platform_admin

COMPLAINT_THRESHOLD = 0.02
FAILURE_THRESHOLD = 3
ZERO_FAILURE_THRESHOLD = 0


@main.route("/platform-admin")
@user_is_platform_admin
def platform_admin_splash_page():
    return render_template(
        "views/platform-admin/splash-page.html",
    )


@main.route("/platform-admin/summary")
@user_is_platform_admin
def platform_admin():
    form = DateFilterForm(request.args, meta={"csrf": False})
    api_args = {}

    form.validate()

    if form.start_date.data:
        api_args["start_date"] = form.start_date.data
        api_args["end_date"] = form.end_date.data or datetime.utcnow().date()

    platform_stats = platform_stats_api_client.get_aggregate_platform_stats(api_args)
    number_of_complaints = complaint_api_client.get_complaint_count(api_args)

    return render_template(
        "views/platform-admin/index.html",
        form=form,
        global_stats=make_columns(platform_stats, number_of_complaints),
    )


@main.route("/platform-admin/download-all-users")
@user_is_platform_admin
def download_all_users():

    # Create a CSV string from the user data
    users = user_api_client.get_all_users_detailed()

    if len(users) == 0:
        return "No data to download."

    output = StringIO()
    header = ["Name", "Email Address", "Phone Number", "Service"]
    fieldnames = ["name", "email_address", "mobile_number", "service"]
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        delimiter=",",
    )
    # Write custom header
    writer.writerow(dict(zip(fieldnames, header)))
    for user in users:
        user_no_commas = {key: value.replace(",", "") for key, value in user.items()}
        if user_no_commas["name"].startswith("e2e"):
            continue
        writer.writerow(user_no_commas)
    csv_data = output.getvalue()

    # Create a direct download response with the CSV data and appropriate headers
    response = Response(csv_data, content_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = "attachment; filename=users.csv"

    return response


def is_over_threshold(number, total, threshold):
    percentage = number / total * 100 if total else 0
    return percentage > threshold


def get_status_box_data(stats, key, label, threshold=FAILURE_THRESHOLD):
    return {
        "number": "{:,}".format(stats["failures"][key]),
        "label": label,
        "failing": is_over_threshold(stats["failures"][key], stats["total"], threshold),
        "percentage": get_formatted_percentage(stats["failures"][key], stats["total"]),
    }


def get_tech_failure_status_box_data(stats):
    stats = get_status_box_data(
        stats, "technical-failure", "technical failures", ZERO_FAILURE_THRESHOLD
    )
    stats.pop("percentage")
    return stats


def make_columns(global_stats, complaints_number):
    return [
        # email
        {
            "black_box": {
                "number": global_stats["email"]["total"],
                "notification_type": "email",
            },
            "other_data": [
                get_tech_failure_status_box_data(global_stats["email"]),
                get_status_box_data(
                    global_stats["email"], "permanent-failure", "permanent failures"
                ),
                get_status_box_data(
                    global_stats["email"], "temporary-failure", "temporary failures"
                ),
                {
                    "number": complaints_number,
                    "label": "complaints",
                    "failing": is_over_threshold(
                        complaints_number,
                        global_stats["email"]["total"],
                        COMPLAINT_THRESHOLD,
                    ),
                    "percentage": get_formatted_percentage_two_dp(
                        complaints_number, global_stats["email"]["total"]
                    ),
                    "url": url_for("main.platform_admin_list_complaints"),
                },
            ],
            "test_data": {
                "number": global_stats["email"]["test-key"],
                "label": "test emails",
            },
        },
        # sms
        {
            "black_box": {
                "number": global_stats["sms"]["total"],
                "notification_type": "sms",
            },
            "other_data": [
                get_tech_failure_status_box_data(global_stats["sms"]),
                get_status_box_data(
                    global_stats["sms"], "permanent-failure", "permanent failures"
                ),
                get_status_box_data(
                    global_stats["sms"], "temporary-failure", "temporary failures"
                ),
            ],
            "test_data": {
                "number": global_stats["sms"]["test-key"],
                "label": "test text messages",
            },
        },
    ]


@main.route("/platform-admin/live-services", endpoint="live_services")
@main.route("/platform-admin/trial-services", endpoint="trial_services")
@user_is_platform_admin
def platform_admin_services():
    form = DateFilterForm(request.args)
    if all(
        (
            request.args.get("include_from_test_key") is None,
            request.args.get("start_date") is None,
            request.args.get("end_date") is None,
        )
    ):
        # Default to True if the user hasn’t done any filtering,
        # otherwise respect their choice
        form.include_from_test_key.data = True

    include_from_test_key = form.include_from_test_key.data
    api_args = {
        "detailed": True,
        "only_active": False,  # specifically DO get inactive services
        "include_from_test_key": include_from_test_key,
    }

    if form.start_date.data:
        api_args["start_date"] = form.start_date.data
        api_args["end_date"] = form.end_date.data or datetime.utcnow().date()

    services = filter_and_sort_services(
        service_api_client.get_services(api_args)["data"],
        trial_mode_services=request.endpoint == "main.trial_services",
    )

    return render_template(
        "views/platform-admin/services.html",
        include_from_test_key=include_from_test_key,
        form=form,
        services=list(format_stats_by_service(services)),
        page_title="{} services".format(
            "Trial mode" if request.endpoint == "main.trial_services" else "Live"
        ),
        global_stats=create_global_stats(services),
    )


@main.route("/platform-admin/reports")
@user_is_platform_admin
def platform_admin_reports():
    return render_template("views/platform-admin/reports.html")


@main.route("/platform-admin/reports/live-services.csv")
@user_is_platform_admin
def live_services_csv():
    results = service_api_client.get_live_services_data()["data"]

    column_names = OrderedDict(
        [
            ("service_id", "Service ID"),
            ("organization_name", "Organization"),
            ("organization_type", "Organization type"),
            ("service_name", "Service name"),
            ("consent_to_research", "Consent to research"),
            ("contact_name", "Main contact"),
            ("contact_email", "Contact email"),
            ("contact_mobile", "Contact mobile"),
            ("live_date", "Live date"),
            ("sms_volume_intent", "SMS volume intent"),
            ("email_volume_intent", "Email volume intent"),
            ("sms_totals", "SMS sent this year"),
            ("email_totals", "Emails sent this year"),
            ("free_sms_fragment_limit", "Free sms allowance"),
        ]
    )

    # initialise with header row
    live_services_data = [[x for x in column_names.values()]]

    for row in results:
        if row["live_date"]:
            row["live_date"] = datetime.strptime(
                row["live_date"], "%a, %d %b %Y %X %Z"
            ).strftime("%d-%m-%Y")

        live_services_data.append([row[api_key] for api_key in column_names.keys()])

    return (
        Spreadsheet.from_rows(live_services_data).as_csv_data,
        200,
        {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": 'inline; filename="{} live services report.csv"'.format(
                format_date_numeric(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
            ),
        },
    )


@main.route(
    "/platform-admin/reports/notifications-sent-by-service", methods=["GET", "POST"]
)
@user_is_platform_admin
def notifications_sent_by_service():
    form = RequiredDateFilterForm()

    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data

        headers = [
            "date_created",
            "service_id",
            "service_name",
            "notification_type",
            "count_sending",
            "count_delivered",
            "count_technical_failure",
            "count_temporary_failure",
            "count_permanent_failure",
            "count_sent",
        ]
        result = notification_api_client.get_notification_status_by_service(
            start_date, end_date
        )
        content_disposition = (
            'attachment; filename="{} to {} notification status '
            'per service report.csv"'.format(start_date, end_date)
        )
        return (
            Spreadsheet.from_rows([headers] + result).as_csv_data,
            200,
            {
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": content_disposition,
            },
        )

    return render_template(
        "views/platform-admin/notifications_by_service.html", form=form
    )


@main.route("/platform-admin/reports/usage-for-all-services", methods=["GET", "POST"])
@user_is_platform_admin
def get_billing_report():
    form = BillingReportDateFilterForm()

    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        headers = [
            "organization_id",
            "organization_name",
            "service_id",
            "service_name",
            "sms_cost",
            "sms_chargeable_units",
            "purchase_order_number",
            "contact_names",
            "contact_email_addresses",
            "billing_reference",
        ]
        try:
            result = billing_api_client.get_data_for_billing_report(
                start_date, end_date
            )
        except HTTPError as e:
            message = "Date must be in a single financial year."
            if e.status_code == 400 and e.message == message:
                flash(message)
                return render_template(
                    "views/platform-admin/get-billing-report.html", form=form
                )
            else:
                raise e
        rows = [
            [
                r["organization_id"],
                r["organization_name"],
                r["service_id"],
                r["service_name"],
                r["sms_cost"],
                r["sms_chargeable_units"],
                r.get("purchase_order_number"),
                r.get("contact_names"),
                r.get("contact_email_addresses"),
                r.get("billing_reference"),
            ]
            for r in result
        ]
        if rows:
            return (
                Spreadsheet.from_rows([headers] + rows).as_csv_data,
                200,
                {
                    "Content-Type": "text/csv; charset=utf-8",
                    "Content-Disposition": 'attachment; filename="Billing Report from {} to {}.csv"'.format(
                        start_date, end_date
                    ),
                },
            )
        else:
            flash("No results for dates")
    return render_template("views/platform-admin/get-billing-report.html", form=form)


@main.route("/platform-admin/reports/get-users-report", methods=["GET", "POST"])
@user_is_platform_admin
def get_users_report():
    headers = [
        "name",
        "services",
        "platform admin",
        "permissions",
        "password changed at",
        "state",
    ]
    try:
        result = user_api_client.get_all_users()

    except HTTPError as e:
        raise e

    rows = []
    for r in result:
        rows.append(_get_user_row(r))
    if rows:
        return (
            Spreadsheet.from_rows([headers] + rows).as_csv_data,
            200,
            {
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": f'attachment; filename="User Report {datetime.utcnow()}.csv"',
            },
        )
    else:
        flash("No results")
    return render_template("views/platform-admin/get-users-report.html")


@main.route("/platform-admin/reports/volumes-by-service", methods=["GET", "POST"])
@user_is_platform_admin
def get_volumes_by_service():
    form = BillingReportDateFilterForm()

    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        headers = [
            "organization id",
            "organization name",
            "service id",
            "service name",
            "free allowance",
            "sms notifications",
            "sms chargeable units",
            "email totals",
        ]
        result = billing_api_client.get_data_for_volumes_by_service_report(
            start_date, end_date
        )

        rows = [
            [
                r["organization_id"],
                r["organization_name"],
                r["service_id"],
                r["service_name"],
                r["free_allowance"],
                r["sms_notifications"],
                r["sms_chargeable_units"],
                r["email_totals"],
            ]
            for r in result
        ]
        if rows:
            return (
                Spreadsheet.from_rows([headers] + rows).as_csv_data,
                200,
                {
                    "Content-Type": "text/csv; charset=utf-8",
                    "Content-Disposition": 'attachment; filename="Volumes by service report from {} to {}.csv"'.format(
                        start_date, end_date
                    ),
                },
            )
        else:
            flash("No results for dates")
    return render_template(
        "views/platform-admin/volumes-by-service-report.html", form=form
    )


@main.route("/platform-admin/reports/daily-volumes-report", methods=["GET", "POST"])
@user_is_platform_admin
def get_daily_volumes():
    form = BillingReportDateFilterForm()

    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        headers = [
            "day",
            "sms totals",
            "sms fragment totals",
            "sms chargeable units",
            "email totals",
        ]
        result = billing_api_client.get_data_for_daily_volumes_report(
            start_date, end_date
        )

        rows = [
            [
                r["day"],
                r["sms_totals"],
                r["sms_fragment_totals"],
                r["sms_chargeable_units"],
                r["email_totals"],
            ]
            for r in result
        ]
        if rows:
            return (
                Spreadsheet.from_rows([headers] + rows).as_csv_data,
                200,
                {
                    "Content-Type": "text/csv; charset=utf-8",
                    "Content-Disposition": 'attachment; filename="Daily volumes report from {} to {}.csv"'.format(
                        start_date, end_date
                    ),
                },
            )
        else:
            flash("No results for dates")
    return render_template("views/platform-admin/daily-volumes-report.html", form=form)


@main.route(
    "/platform-admin/reports/daily-sms-provider-volumes-report", methods=["GET", "POST"]
)
@user_is_platform_admin
def get_daily_sms_provider_volumes():
    form = BillingReportDateFilterForm()

    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        headers = [
            "day",
            "provider",
            "sms totals",
            "sms fragment totals",
            "sms chargeable units",
            "sms cost",
        ]
        result = billing_api_client.get_data_for_daily_sms_provider_volumes_report(
            start_date, end_date
        )

        rows = [
            [
                r["day"],
                r["provider"],
                r["sms_totals"],
                r["sms_fragment_totals"],
                r["sms_chargeable_units"],
                r["sms_cost"],
            ]
            for r in result
        ]
        content_disp = f'attachment; filename="Daily SMS provider volumes report from {start_date} to {end_date}.csv"'
        if rows:
            return (
                Spreadsheet.from_rows([headers] + rows).as_csv_data,
                200,
                {
                    "Content-Type": "text/csv; charset=utf-8",
                    "Content-Disposition": content_disp,
                },
            )
        else:
            flash("No results for dates")
    return render_template(
        "views/platform-admin/daily-sms-provider-volumes-report.html", form=form
    )


@main.route("/platform-admin/complaints")
@user_is_platform_admin
def platform_admin_list_complaints():
    page = get_page_from_request()
    if page is None:
        abort(404, "Invalid page argument ({}).".format(request.args.get("page")))

    response = complaint_api_client.get_all_complaints(page=page)

    prev_page = None
    if response["links"].get("prev"):
        prev_page = generate_previous_dict(
            "main.platform_admin_list_complaints", None, page
        )
    next_page = None
    if response["links"].get("next"):
        next_page = generate_next_dict(
            "main.platform_admin_list_complaints", None, page
        )

    return render_template(
        "views/platform-admin/complaints.html",
        complaints=response["complaints"],
        page=page,
        prev_page=prev_page,
        next_page=next_page,
    )


@main.route("/platform-admin/clear-cache", methods=["GET", "POST"])
@user_is_platform_admin
def clear_cache():
    # note: `service-{uuid}-templates` cache is cleared for both services and templates.
    CACHE_KEYS = OrderedDict(
        [
            (
                "user",
                [
                    "user-????????-????-????-????-????????????",
                ],
            ),
            (
                "service",
                [
                    "has_jobs-????????-????-????-????-????????????",
                    "service-????????-????-????-????-????????????",
                    "service-????????-????-????-????-????????????-templates",
                    "service-????????-????-????-????-????????????-data-retention",
                    "service-????????-????-????-????-????????????-template-folders",
                ],
            ),
            (
                "template",
                [
                    "service-????????-????-????-????-????????????-templates",
                    "service-????????-????-????-????-????????????-template-????????-????-????-????-????????????-version-*",  # noqa
                    "service-????????-????-????-????-????????????-template-????????-????-????-????-????????????-versions",  # noqa
                ],
            ),
            (
                "organization",
                [
                    "organizations",
                    "domains",
                    "live-service-and-organization-counts",
                    "organization-????????-????-????-????-????????????-name",
                ],
            ),
        ]
    )

    form = AdminClearCacheForm()

    form.model_type.choices = [
        (key, key.replace("_", " ").title()) for key in CACHE_KEYS
    ]

    if form.validate_on_submit():
        group_keys = form.model_type.data
        groups = map(CACHE_KEYS.get, group_keys)
        patterns = list(itertools.chain(*groups))

        num_deleted = sum(
            redis_client.delete_by_pattern(pattern) for pattern in patterns
        )

        msg = (
            f"Removed {num_deleted} objects "
            f"across {len(patterns)} key formats "
            f'for {", ".join(group_keys)}'
        )

        flash(msg, category="default")

    return render_template("views/platform-admin/clear-cache.html", form=form)


def sum_service_usage(service):
    total = 0
    for notification_type in service["statistics"].keys():
        total += service["statistics"][notification_type]["requested"]
    return total


def filter_and_sort_services(services, trial_mode_services=False):
    return [
        service
        for service in sorted(
            services,
            key=lambda service: (
                service["active"],
                sum_service_usage(service),
                service["created_at"],
            ),
            reverse=True,
        )
        if service["restricted"] == trial_mode_services
    ]


def create_global_stats(services):
    stats = {
        "email": {"delivered": 0, "failed": 0, "requested": 0},
        "sms": {"delivered": 0, "failed": 0, "requested": 0},
    }
    # Issue #1323. The back end is now sending 'failure' instead of
    # 'failed'.  Adjust it here, but keep it flexible in case
    # the backend reverts to 'failed'.
    for service in services:
        if service["statistics"]["sms"].get("failure") is not None:
            service["statistics"]["sms"]["failed"] = service["statistics"]["sms"][
                "failure"
            ]
        if service["statistics"]["email"].get("failure") is not None:
            service["statistics"]["email"]["failed"] = service["statistics"]["email"][
                "failure"
            ]

    for service in services:

        for msg_type, status in itertools.product(
            ("sms", "email"), ("delivered", "failed", "requested")
        ):
            stats[msg_type][status] += service["statistics"][msg_type][status]

    for stat in stats.values():
        stat["failure_rate"] = get_formatted_percentage(
            stat["failed"], stat["requested"]
        )
    return stats


def format_stats_by_service(services):
    for service in services:
        yield {
            "id": service["id"],
            "name": service["name"],
            "stats": service["statistics"],
            "restricted": service["restricted"],
            "created_at": service["created_at"],
            "active": service["active"],
        }


def _get_user_row(r):
    # [{
    #     'name': 'Kenneth Kehl',
    #     'organizations': [],
    #     'password_changed_at': '2023-07-21 14:12:54.832850', 'permissions': {
    #     '672b8a66-e22e-40f6-b1e5-39cc1c6bf857': ['manage_users', 'manage_templates', 'manage_settings', 'send_texts',
    #                                               'send_emails', 'manage_api_keys', 'view_activity']},
    #     'platform_admin': True, 'services': ['672b8a66-e22e-40f6-b1e5-39cc1c6bf857'], 'state': 'active'}]

    row = []
    row.append(r["name"])

    service_id_name_lookup = {}
    services = []
    for s in r["services"]:
        my_service = service_api_client.get_service(s)
        service_id_name_lookup[my_service["data"]["id"]] = my_service["data"]["name"]
        services.append(my_service["data"]["name"])
    services = str(services)
    services = services.replace("[", "")
    services = services.replace("]", "")
    row.append(services)
    row.append(r["platform_admin"])
    permissions = r["permissions"]
    for k, v in service_id_name_lookup.items():
        if permissions.get(k):
            permissions[v] = permissions[k]
            del permissions[k]

    permissions = json.dumps(permissions, indent=4)
    row.append(permissions)
    row.append(r["password_changed_at"])
    row.append(r["state"])
    return row


@main.route(
    "/platform-admin/load-test",
    methods=["POST", "GET"],
)
@user_is_platform_admin
def load_test():
    """
    The load test assumes that a service called 'Test service' exists.  It will make
    the platform admin a member of this service if the platform is not already. All
    messagese will be sent in this service.
    """
    service = _find_load_test_service()
    _prepare_load_test_service(service)
    example_template = _find_example_template(service)

    # Simulated success
    for _ in range(0, 250):
        session["recipient"] = current_app.config["SIMULATED_SMS_NUMBERS"][0]
        session["placeholders"] = {
            "day of week": "Monday",
            "color": "blue",
            "phone number": current_app.config["SIMULATED_SMS_NUMBERS"][0],
        }
        _send_notification(service["id"], example_template["id"])
    # Simulated failure
    for _ in range(0, 250):
        session["recipient"] = current_app.config["SIMULATED_SMS_NUMBERS"][1]
        session["placeholders"] = {
            "day of week": "Wednesday",
            "color": "orange",
            "phone number": current_app.config["SIMULATED_SMS_NUMBERS"][1],
        }
        _send_notification(service["id"], example_template["id"])

    # For now, just hang out on the platform admin page
    return redirect(request.referrer)


def _find_example_template(service):
    templates = service_api_client.get_service_templates(service["id"])
    templates = templates["data"]
    for template in templates:
        # template = json.loads(template)
        if template["name"] == "Example text message template":
            return template

    raise Exception("Could not find example template for load test")


def _find_load_test_service():
    services = service_api_client.find_services_by_name("Test service")
    services = services["data"]

    for service in services:
        if service["name"] == "Test service":
            return service

    raise Exception("Could not find 'Test service' for load test")


def _prepare_load_test_service(service):
    users = user_api_client.get_all_users()
    for user in users:
        if user["platform_admin"] == "t":
            try:
                user_api_client.add_user_to_service(
                    service["id"], user["id"], ["send messages"]
                )
            except Exception:
                current_app.logger.exception(
                    "Couldnt add user, may already be part of service"
                )
                pass
