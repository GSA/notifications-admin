from flask import (
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user

from app import status_api_client
from app.formatters import apply_html_class, convert_markdown_template
from app.main import main
from app.main.views.pricing import CURRENT_SMS_RATE
from app.main.views.sub_navigation_dictionaries import (
    about_notify_nav,
    using_notify_nav,
)
from app.utils.user import user_is_logged_in


# Hook to check for feature flags
@main.before_request
def check_feature_flags():
    # Placeholder for future feature flag checks
    # Example:
    if "/jobs" in request.path and not current_app.config.get(
        "FEATURE_SOCKET_ENABLED", False
    ):
        abort(404)
    pass


@main.route("/test/feature-flags")
def test_feature_flags():
    return jsonify(
        {"FEATURE_SOCKET_ENABLED": current_app.config["FEATURE_SOCKET_ENABLED"]}
    )


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
    markdown = convert_markdown_template("get-started")
    html_style = apply_html_class(
        [
            ["ol", "usa-process-list"],
            ["li", "usa-process-list__item padding-bottom-4 margin-top-2"],
            ["h2", "usa-process-list__heading line-height-sans-3"],
        ],
        markdown,
    )

    return render_template(
        "views/get-started.html",
        navigation_links=using_notify_nav(),
        content=html_style,
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


@main.route("/using-notify/best-practices")
@user_is_logged_in
def best_practices():
    return render_template(
        "views/guides/best-practices.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/best-practices/clear-goals")
@user_is_logged_in
def clear_goals():
    return render_template(
        "views/guides/clear-goals.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/best-practices/rules-and-regulations")
@user_is_logged_in
def rules_and_regulations():
    return render_template(
        "views/guides/rules-and-regulations.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/best-practices/establish-trust")
@user_is_logged_in
def establish_trust():
    return render_template(
        "views/guides/establish-trust.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/best-practices/write-for-action")
@user_is_logged_in
def write_for_action():
    return render_template(
        "views/guides/write-for-action.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/best-practices/multiple-languages")
@user_is_logged_in
def multiple_languages():
    return render_template(
        "views/guides/multiple-languages.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/best-practices/benchmark-performance")
@user_is_logged_in
def benchmark_performance():
    return render_template(
        "views/guides/benchmark-performance.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/how-to")
@user_is_logged_in
def how_to():
    return render_template(
        "views/how-to/index.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/contact")
def contact():
    return render_template(
        "views/contact.html",
        navigation_links=about_notify_nav(),
    )


@main.route("/about")
def about_notify():
    return render_template(
        "views/about/about.html",
        navigation_links=about_notify_nav(),
    )


@main.route("/about/security")
def about_security():
    return render_template(
        "views/about/security.html",
        navigation_links=about_notify_nav(),
    )


@main.route("/about/why-text-messaging")
def why_text_messaging():
    return render_template(
        "views/about/why-text-messaging.html",
        navigation_links=about_notify_nav(),
    )


@main.route("/notify-service-ending")
@user_is_logged_in
def notify_service_ending():
    return render_template(
        "views/notify-service-ending.html",
    )


@main.route("/using-notify/how-to/create-and-send-messages")
@user_is_logged_in
def create_and_send_messages():
    return render_template(
        "views/how-to/create-and-send-messages.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/how-to/edit-and-format-messages")
@user_is_logged_in
def edit_and_format_messages():
    return render_template(
        "views/how-to/edit-and-format-messages.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/using-notify/how-to/send-files-by-email")
@user_is_logged_in
def send_files_by_email():
    return render_template(
        "views/how-to/send-files-by-email.html",
        navigation_links=using_notify_nav(),
    )


@main.route("/studio")
def studio():
    return render_template(
        "views/studio.html",
    )


@main.route("/acceptable-use-policy")
def acceptable_use_policy():
    return render_template(
        "views/acceptable-use-policy.html",
    )


# --- Redirects --- #


@main.route("/information-security", endpoint="information_security")
@main.route("/using_notify", endpoint="old_using_notify")
@main.route("/information-risk-management", endpoint="information_risk_management")
@main.route("/integration_testing", endpoint="old_integration_testing")
def old_page_redirects():
    redirects = {
        "main.information_security": "main.using_notify",
        "main.old_using_notify": "main.using_notify",
        "main.information_risk_management": "main.security",
        "main.old_integration_testing": "main.integration_testing",
    }
    return redirect(url_for(redirects[request.endpoint]), code=301)
