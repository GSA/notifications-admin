import json

from app.extensions import redis_client
from app.notify_client import NotifyAdminAPIClient


class BillingAPIClient(NotifyAdminAPIClient):
    def get_monthly_usage_for_service(self, service_id, year):
        monthly_usage = redis_client.get(f"monthly-usage-summary-{service_id}-{year}")
        if monthly_usage is not None:
            return json.loads(monthly_usage.decode("utf-8"))
        result = self.get(
            "/service/{0}/billing/monthly-usage".format(service_id),
            params=dict(year=year),
        )
        redis_client.set(
            f"monthly-usage-summary-{service_id}-{year}",
            json.dumps(result),
            ex=30,
        )
        return result

    def get_annual_usage_for_service(self, service_id, year=None):
        annual_usage = redis_client.get(f"yearly-usage-summary-{service_id}-{year}")
        if annual_usage is not None:
            return json.loads(annual_usage.decode("utf-8"))
        result = self.get(
            "/service/{0}/billing/yearly-usage-summary".format(service_id),
            params=dict(year=year),
        )

        redis_client.set(
            f"yearly-usage-summary-{service_id}-{year}",
            json.dumps(result),
            ex=30,
        )
        return result

    def get_free_sms_fragment_limit_for_year(self, service_id, year=None):
        frag_limit = redis_client.get(f"free-sms-fragment-limit-{service_id}-{year}")
        if frag_limit is not None:
            return json.loads(frag_limit.decode("utf-8"))
        result = self.get(
            "/service/{0}/billing/free-sms-fragment-limit".format(service_id),
            params=dict(financial_year_start=year),
        )

        redis_client.set(
            f"free-sms-fragment-limit-{service_id}-{year}",
            json.dumps(result["free_sms_fragment_limit"]),
            ex=30,
        )
        return result["free_sms_fragment_limit"]

    def create_or_update_free_sms_fragment_limit(
        self, service_id, free_sms_fragment_limit, year=None
    ):
        # year = None will update current and future year in the API
        data = {
            "financial_year_start": year,
            "free_sms_fragment_limit": free_sms_fragment_limit,
        }

        return self.post(
            url="/service/{0}/billing/free-sms-fragment-limit".format(service_id),
            data=data,
        )

    def get_data_for_billing_report(self, start_date, end_date):
        x_start_date = str(start_date)
        x_start_date = x_start_date.replace(" ", "_")
        x_end_date = str(end_date)
        x_end_date = x_end_date.replace(" ", "_")
        billing_data = redis_client.get(
            f"get-data-for-billing-report-{x_start_date}-{x_end_date}"
        )
        if billing_data is not None:
            return json.loads(billing_data.decode("utf-8"))
        result = self.get(
            url="/platform-stats/data-for-billing-report",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
            },
        )
        redis_client.set(
            f"get-data-for-billing-report-{x_start_date}-{x_end_date}",
            json.dumps(result),
            ex=30,
        )
        return result

    def get_data_for_volumes_by_service_report(self, start_date, end_date):
        return self.get(
            url="/platform-stats/volumes-by-service",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
            },
        )

    def get_data_for_daily_volumes_report(self, start_date, end_date):
        return self.get(
            url="/platform-stats/daily-volumes-report",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
            },
        )

    def get_data_for_daily_sms_provider_volumes_report(self, start_date, end_date):
        return self.get(
            url="/platform-stats/daily-sms-provider-volumes-report",
            params={
                "start_date": str(start_date),
                "end_date": str(end_date),
            },
        )


billing_api_client = BillingAPIClient()
