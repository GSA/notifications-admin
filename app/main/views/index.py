import os
import secrets
from urllib.parse import unquote

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

from app import redis_client, status_api_client
from app.formatters import apply_html_class, convert_markdown_template
from app.main import main
from app.main.views.pricing import CURRENT_SMS_RATE
from app.main.views.sub_navigation_dictionaries import (
    about_notify_nav,
    best_practices_nav,
    features_nav,
    using_notify_nav,
)
from app.utils.user import user_is_logged_in
from notifications_utils.url_safe_token import generate_token


# Hook to check for feature flags
@main.before_request
def check_feature_flags():
    if request.path.startswith("/guides/best-practices") and not current_app.config.get(
        "FEATURE_BEST_PRACTICES_ENABLED", False
    ):
        abort(404)

    if request.path.startswith("/about") and not current_app.config.get(
        "FEATURE_ABOUT_PAGE_ENABLED", False
    ):
        abort(404)


@main.route("/test/feature-flags")
def test_feature_flags():
    return jsonify(
        {
            "FEATURE_BEST_PRACTICES_ENABLED": current_app.config[
                "FEATURE_BEST_PRACTICES_ENABLED"
            ]
        }
    )


@main.route("/")
def index():
    if current_user and current_user.is_authenticated:
        return redirect(url_for("main.choose_account"))

    ttl = 24 * 60 * 60

    # make and store the state
    state = generate_token(
        str(request.remote_addr),
        current_app.config["SECRET_KEY"],
        current_app.config["DANGEROUS_SALT"],
    )
    state_key = f"login-state-{unquote(state)}"
    redis_client.set(state_key, state, ex=ttl)

    # make and store the nonce
    nonce = secrets.token_urlsafe()
    nonce_key = f"login-nonce-{unquote(nonce)}"
    redis_client.set(nonce_key, nonce, ex=ttl)

    url = os.getenv("LOGIN_DOT_GOV_INITIAL_SIGNIN_URL")
    if url is not None:
        url = url.replace("NONCE", nonce)
        url = url.replace("STATE", state)
    return render_template(
        "views/signedout.html",
        sms_rate=CURRENT_SMS_RATE,
        counts=status_api_client.get_count_of_live_services_and_organizations(),
        initial_signin_url=url,
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


@main.route("/guides/best-practices")
@user_is_logged_in
def best_practices():
    return render_template(
        "views/best-practices/best-practices.html",
        navigation_links=best_practices_nav(),
    )


@main.route("/guides/best-practices/clear-goals")
@user_is_logged_in
def clear_goals():
    return render_template(
        "views/best-practices/clear-goals.html",
        navigation_links=best_practices_nav(),
    )


@main.route("/guides/best-practices/rules-and-regulations")
@user_is_logged_in
def rules_and_regulations():
    return render_template(
        "views/best-practices/rules-and-regulations.html",
        navigation_links=best_practices_nav(),
    )


@main.route("/guides/best-practices/establish-trust")
@user_is_logged_in
def establish_trust():
    return render_template(
        "views/best-practices/establish-trust.html",
        navigation_links=best_practices_nav(),
    )


@main.route("/guides/best-practices/write-for-action")
@user_is_logged_in
def write_for_action():
    return render_template(
        "views/best-practices/write-for-action.html",
        navigation_links=best_practices_nav(),
    )


@main.route("/guides/best-practices/multiple-languages")
@user_is_logged_in
def multiple_languages():
    return render_template(
        "views/best-practices/multiple-languages.html",
        navigation_links=best_practices_nav(),
    )


@main.route("/guides/best-practices/benchmark-performance")
@user_is_logged_in
def benchmark_performance():
    return render_template(
        "views/best-practices/benchmark-performance.html",
        navigation_links=best_practices_nav(),
    )


@main.route("/using-notify/guidance")
@main.route("/guides/using-notify/guidance")
@user_is_logged_in
def guidance_index():
    return render_template(
        "views/guidance/index.html",
        navigation_links=using_notify_nav(),
        feature_best_practices_enabled=current_app.config[
            "FEATURE_BEST_PRACTICES_ENABLED"
        ],
    )


@main.route("/about")
def about_notify():
    return render_template(
        "views/about/about.html",
        navigation_links=about_notify_nav(),
    )


@main.route("/about/why-text-messaging")
def why_text_messaging():
    return render_template(
        "views/about/why-text-messaging.html",
        navigation_links=about_notify_nav(),
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
@main.route("/information-security", endpoint="information_security")
@main.route("/using_notify", endpoint="old_using_notify")
@main.route("/information-risk-management", endpoint="information_risk_management")
@main.route("/integration_testing", endpoint="old_integration_testing")
def old_page_redirects():
    redirects = {
        "main.old_roadmap": "main.roadmap",
        "main.information_security": "main.using_notify",
        "main.old_using_notify": "main.using_notify",
        "main.information_risk_management": "main.security",
        "main.old_integration_testing": "main.integration_testing",
    }
    return redirect(url_for(redirects[request.endpoint]), code=301)
