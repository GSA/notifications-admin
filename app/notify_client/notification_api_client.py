from app.notify_client import NotifyAdminAPIClient, _attach_current_user


class NotificationApiClient(NotifyAdminAPIClient):

    def get_notifications_for_service(
        self,
        service_id,
        job_id=None,
        template_type=None,
        status=None,
        page=None,
        page_size=None,
        count_pages=None,
        limit_days=None,
        include_jobs=None,
        include_from_test_key=None,
        format_for_csv=None,
        to=None,
        include_one_off=None,
    ):
        params = {
            'page': page,
            'page_size': page_size,
            'template_type': template_type,
            'status': status,
            'include_jobs': include_jobs,
            'include_from_test_key': include_from_test_key,
            'format_for_csv': format_for_csv,
            'to': to,
            'include_one_off': include_one_off,
            'count_pages': count_pages,
        }

        params = {k: v for k, v in params.items() if v is not None}

        # if `to` is set it is likely PII like an email address or mobile which
        # we do not want in our logs, so we do a POST request instead of a GET
        method = self.post if to else self.get
        kwargs = {'data': params} if to else {'params': params}

        if job_id:
            return method(
                url='/service/{}/job/{}/notifications'.format(service_id, job_id),
                **kwargs
            )
        else:
            if limit_days is not None:
                params['limit_days'] = limit_days
            return method(
                url='/service/{}/notifications'.format(service_id),
                **kwargs
            )

    def send_notification(self, service_id, *, template_id, recipient, personalisation, sender_id):
        data = {
            'template_id': template_id,
            'to': recipient,
            'personalisation': personalisation,
        }
        if sender_id:
            data['sender_id'] = sender_id
        data = _attach_current_user(data)
        return self.post(url='/service/{}/send-notification'.format(service_id), data=data)

    def get_notification(self, service_id, notification_id):
        return self.get(url='/service/{}/notifications/{}'.format(service_id, notification_id))

    def get_api_notifications_for_service(self, service_id):
        ret = self.get_notifications_for_service(
            service_id,
            include_jobs=False,
            include_from_test_key=True,
            include_one_off=False,
            count_pages=False
        )
        return ret

    def update_notification_to_cancelled(self, service_id, notification_id):
        return self.post(
            url='/service/{}/notifications/{}/cancel'.format(service_id, notification_id),
            data={})

    def get_notification_status_by_service(self, start_date, end_date):
        return self.get(
            url='service/monthly-data-by-service',
            params={
                'start_date': str(start_date),
                'end_date': str(end_date),
            }
        )

    def get_notification_count_for_job_id(self, *, service_id, job_id):
        return self.get(url='/service/{}/job/{}/notification_count'.format(service_id, job_id))["count"]


notification_api_client = NotificationApiClient()
