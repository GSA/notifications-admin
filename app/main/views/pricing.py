from flask import render_template

from app.main import main
from app.main.forms import SearchByNameForm
from app.main.views.sub_navigation_dictionaries import using_notify_nav
from app.utils.user import user_is_logged_in
from notifications_utils.international_billing_rates import INTERNATIONAL_BILLING_RATES

CURRENT_SMS_RATE = "1.72"


@main.route("/using-notify/pricing")
@user_is_logged_in
def pricing():
    return render_template(
        "views/pricing/index.html",
        sms_rate=CURRENT_SMS_RATE,
        international_sms_rates=sorted(
            [
                (cc, country["names"], country["billable_units"])
                for cc, country in INTERNATIONAL_BILLING_RATES.items()
            ],
            key=lambda x: x[0],
        ),
        search_form=SearchByNameForm(),
        navigation_links=using_notify_nav(),
    )


@main.route("/pricing/how-to-pay")
@user_is_logged_in
def how_to_pay():
    return render_template(
        "views/pricing/how-to-pay.html",
        navigation_links=using_notify_nav(),
    )
