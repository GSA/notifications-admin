import datetime
from zoneinfo import ZoneInfo

from app.extensions import redis_client
from app.notify_client import NotifyAdminAPIClient, _attach_current_user, cache
from app.utils.csv import get_user_preferred_timezone


class JobApiClient(NotifyAdminAPIClient):
    JOB_STATUSES = {
        "scheduled",
        "pending",
        "in progress",
        "finished",
        "cancelled",
        "sending limits exceeded",
        "ready to send",
        "sent to dvla",
    }
    SCHEDULED_JOB_STATUS = "scheduled"
    CANCELLED_JOB_STATUS = "cancelled"
    NON_CANCELLED_JOB_STATUSES = JOB_STATUSES - {CANCELLED_JOB_STATUS}
    NON_SCHEDULED_JOB_STATUSES = JOB_STATUSES - {
        SCHEDULED_JOB_STATUS,
        CANCELLED_JOB_STATUS,
    }

    def get_job(self, service_id, job_id):
        params = {}
        job = self.get(
            url="/service/{}/job/{}".format(service_id, job_id), params=params
        )

        return job

    def get_jobs(self, service_id, *, limit_days=None, statuses=None, page=1):
        params = {"page": page}
        if limit_days is not None:
            params["limit_days"] = limit_days
        if statuses is not None:
            params["statuses"] = ",".join(statuses)

        return self.get(url="/service/{}/job".format(service_id), params=params)

    def get_uploads(self, service_id, limit_days=None, page=1):
        params = {"page": page}
        if limit_days is not None:
            params["limit_days"] = limit_days
        return self.get(url="/service/{}/upload".format(service_id), params=params)

    def has_sent_previously(
        self, service_id, template_id, template_version, original_file_name
    ):
        return (template_id, template_version, original_file_name) in (
            (
                job["template"],
                job["template_version"],
                job["original_file_name"],
            )
            for job in self.get_jobs(service_id, limit_days=0)["data"]
            if job["job_status"] != "cancelled"
        )

    def get_page_of_jobs(self, service_id, *, page, statuses=None, limit_days=None):
        return self.get_jobs(
            service_id,
            statuses=statuses or self.NON_SCHEDULED_JOB_STATUSES,
            page=page,
            limit_days=limit_days,
        )

    def get_immediate_jobs(self, service_id):
        return self.get_jobs(
            service_id,
            limit_days=7,
            statuses=self.NON_SCHEDULED_JOB_STATUSES,
        )["data"]

    def get_scheduled_jobs(self, service_id):
        return sorted(
            self.get_jobs(service_id, statuses=[self.SCHEDULED_JOB_STATUS])["data"],
            key=lambda job: job["scheduled_for"],
            reverse=True,
        )

    def get_scheduled_job_stats(self, service_id):
        return self.get(url=f"/service/{service_id}/job/scheduled-job-stats")

    @cache.set("has_jobs-{service_id}")
    def has_jobs(self, service_id):
        return bool(self.get_jobs(service_id)["data"])

    @classmethod
    def convert_user_time_to_utc(cls, scheduled_for):
        user_preferred_tz = get_user_preferred_timezone()

        user_date = datetime.datetime.fromisoformat(scheduled_for)
        scheduled_for = (
            user_date.replace(tzinfo=ZoneInfo(user_preferred_tz))
            .astimezone(ZoneInfo("UTC"))
            .strftime("%Y-%m-%dT%H:%M:%S")
        )

        return scheduled_for

    def create_job(self, job_id, service_id, scheduled_for=None):
        data = {"id": job_id}

        # make a datetime object in the user's preferred timezone

        if scheduled_for:
            scheduled_for = JobApiClient.convert_user_time_to_utc(scheduled_for)
            data.update({"scheduled_for": scheduled_for})

        data = _attach_current_user(data)
        job = self.post(url="/service/{}/job".format(service_id), data=data)

        redis_client.set(
            "has_jobs-{}".format(service_id),
            b"true",
            ex=int(cache.DEFAULT_TTL),
        )

        return job

    @cache.delete("has_jobs-{service_id}")
    def cancel_job(self, service_id, job_id):
        return self.post(
            url="/service/{}/job/{}/cancel".format(service_id, job_id), data={}
        )


job_api_client = JobApiClient()
