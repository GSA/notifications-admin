from datetime import datetime, timedelta
from itertools import groupby
from operator import itemgetter
from statistics import mean

import pytz
from flask import render_template

from app import performance_dashboard_api_client, status_api_client
from app.main import main
from app.utils.csv import get_user_preferred_timezone


@main.route("/performance")
def performance():
    preferred_tz = pytz.timezone(get_user_preferred_timezone())
    stats = performance_dashboard_api_client.get_performance_dashboard_stats(
        start_date=(datetime.now(preferred_tz) - timedelta(days=7)).date(),
        end_date=datetime.now(preferred_tz).date(),
    )
    stats["organizations_using_notify"] = sorted(
        [
            {
                "organization_name": organization_name or "No organization",
                "count_of_live_services": len(list(group)),
            }
            for organization_name, group in groupby(
                stats["services_using_notify"],
                itemgetter("organization_name"),
            )
        ],
        key=itemgetter("organization_name"),
    )
    stats["average_percentage_under_10_seconds"] = mean(
        [row["percentage_under_10_seconds"] for row in stats["processing_time"]] or [0]
    )
    stats["count_of_live_services_and_organizations"] = (
        status_api_client.get_count_of_live_services_and_organizations()
    )

    return render_template("views/performance.html", **stats)
