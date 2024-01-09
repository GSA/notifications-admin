from flask import abort, redirect, render_template, request, url_for
from flask_login import current_user

from app import status_api_client
from app.formatters import apply_html_class, convert_markdown_template
from app.main import main
from app.main.views.pricing import CURRENT_SMS_RATE
from app.main.views.sub_navigation_dictionaries import features_nav, using_notify_nav
from app.utils.user import user_is_logged_in


@main.route("/")
def index():
    if current_user and current_user.is_authenticated:
        return redirect(url_for("main.choose_account"))

    return render_template(
        "views/signedout.html",
        sms_rate=CURRENT_SMS_RATE,
        counts=status_api_client.get_count_of_live_services_and_organizations(),
    )


@main.route("/error/<int:status_code>")
def error(status_code):
    if status_code >= 500:
        abort(404)
    abort(status_code)


@main.route("/privacy")
@user_is_logged_in
def privacy():
    return render_template("views/privacy.html")


@main.route("/accessibility-statement")
@user_is_logged_in
def accessibility_statement():
    return render_template("views/accessibility_statement.html")


@main.route("/delivery-and-failure")
@main.route("/features/messages-status")
def delivery_and_failure():
    return redirect(url_for(".message_status"), 301)


@main.route("/design-patterns-content-guidance")
@user_is_logged_in
def design_content():
    return redirect(
        "https://www.gov.uk/service-manual/design/sending-emails-and-text-messages", 301
    )


@main.route("/documentation")
@user_is_logged_in
def documentation():
    return render_template(
        "views/documentation.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/integration-testing")
def integration_testing():
    return render_template("views/integration-testing.html"), 410


@main.route("/callbacks")
def callbacks():
    return redirect(url_for("main.documentation"), 301)


# --- Features page set --- #


@main.route("/features")
@user_is_logged_in
def features():
    return render_template("views/features.html", navigation_links=features_nav())


@main.route("/features/roadmap", endpoint="roadmap")
@user_is_logged_in
def roadmap():
    return render_template("views/roadmap.html", navigation_links=features_nav())


@main.route("/features/sms")
@user_is_logged_in
def features_sms():
    return render_template(
        "views/features/text-messages.html", navigation_links=features_nav()
    )


@main.route("/features/security", endpoint="security")
@user_is_logged_in
def security():
    return render_template("views/security.html", navigation_links=features_nav())


@main.route("/features/terms", endpoint="terms")
@user_is_logged_in
def terms():
    return render_template(
        "views/terms-of-use.html",
        navigation_links=features_nav(),
    )


@main.route("/features/using_notify")
@user_is_logged_in
def using_notify():
    return (
        render_template("views/using-notify.html", navigation_links=features_nav()),
        410,
    )


@main.route("/using-notify/delivery-status")
@user_is_logged_in
def message_status():
    return render_template(
        "views/message-status.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/features/get-started")
@user_is_logged_in
def get_started_old():
    return redirect(url_for(".get_started"), 301)


@main.route("/using-notify/get-started")
@user_is_logged_in
def get_started():
    markdown = convert_markdown_template('get-started')
    html_style = apply_html_class([['ol', 'usa-process-list'],
                                   ['li', 'usa-process-list__item padding-bottom-4 margin-top-2'],
                                   ['h2', 'usa-process-list__heading line-height-sans-3']],
                                  markdown)

    return render_template(
        "views/get-started.html",
        navigation_links=using_notify_nav(),
        content=html_style
    )


@main.route("/using-notify/who-its-for")
def who_its_for():
    return redirect(url_for(".features"), 301)


@main.route("/trial-mode")
@main.route("/features/trial-mode")
def trial_mode():
    return redirect(url_for(".trial_mode_new"), 301)


@main.route("/using-notify/trial-mode")
def trial_mode_new():
    return render_template(
        "views/trial-mode.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/guidance")
@user_is_logged_in
def guidance_index():
    return render_template(
        "views/guidance/index.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/guidance/create-and-send-messages")
@user_is_logged_in
def create_and_send_messages():
    return render_template(
        "views/guidance/create-and-send-messages.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/guidance/edit-and-format-messages")
@user_is_logged_in
def edit_and_format_messages():
    return render_template(
        "views/guidance/edit-and-format-messages.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/guidance/send-files-by-email")
@user_is_logged_in
def send_files_by_email():
    return render_template(
        "views/guidance/send-files-by-email.html",
        navigation_links=using_notify_nav(),
    )


# --- Redirects --- #


@main.route("/roadmap", endpoint="old_roadmap")
@main.route("/terms", endpoint="old_terms")
@main.route("/information-security", endpoint="information_security")
@main.route("/using_notify", endpoint="old_using_notify")
@main.route("/information-risk-management", endpoint="information_risk_management")
@main.route("/integration_testing", endpoint="old_integration_testing")
def old_page_redirects():
    redirects = {
        "main.old_roadmap": "main.roadmap",
        "main.old_terms": "main.terms",
        "main.information_security": "main.using_notify",
        "main.old_using_notify": "main.using_notify",
        "main.information_risk_management": "main.security",
        "main.old_integration_testing": "main.integration_testing",
    }
    return redirect(url_for(redirects[request.endpoint]), code=301)
