import json
from datetime import datetime, timezone

from flask import current_app

from app.enums import ServicePermission
from app.extensions import redis_client
from app.notify_client import NotifyAdminAPIClient, _attach_current_user, cache


class ServiceAPIClient(NotifyAdminAPIClient):
    @cache.delete("user-{user_id}")
    def create_service(
        self,
        service_name,
        organization_type,
        message_limit,
        restricted,
        user_id,
        email_from,
    ):
        """
        Create a service and return the json.
        """
        data = {
            "name": service_name,
            "organization_type": organization_type,
            "active": True,
            "message_limit": message_limit,
            "user_id": user_id,
            "restricted": restricted,
            "email_from": email_from,
        }
        data = _attach_current_user(data)
        return self.post("/service", data)["data"]["id"]

    @cache.set("service-{service_id}")
    def get_service(self, service_id):
        """
        Retrieve a service.
        """
        return self.get("/service/{0}".format(service_id))

    def get_service_statistics(self, service_id, limit_days=None):
        return self.get(
            "/service/{0}/statistics".format(service_id),
            params={"limit_days": limit_days},
        )["data"]

    def get_service_notification_statistics_by_day(
        self, service_id, start_date=None, days=None
    ):
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")

        return self.get(
            "/service/{0}/statistics/{1}/{2}".format(service_id, start_date, days),
        )["data"]

    def get_user_service_notification_statistics_by_day(
        self, service_id, user_id, start_date=None, days=None
    ):
        if start_date is None:
            start_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        return self.get(
            "/service/{0}/statistics/user/{1}/{2}/{3}".format(
                service_id, user_id, start_date, days
            ),
        )["data"]

    def get_services(self, params_dict=None):
        """
        Retrieve a list of services.
        """
        return self.get("/service", params=params_dict)

    def find_services_by_name(self, service_name):
        return self.get(
            "/service/find-services-by-name", params={"service_name": service_name}
        )

    def get_live_services_data(self, params_dict=None):
        """
        Retrieve a list of live services data with contact names and notification counts.
        """
        try:
            return self.get("/service/live-services-data", params=params_dict)
        except Exception as e:
            current_app.logger.error(
                f"Error getting live services data {str(e)}", exc_info=True
            )
            raise e

    def get_active_services(self, params_dict=None):
        """
        Retrieve a list of active services.
        """
        params_dict["only_active"] = True
        return self.get_services(params_dict)

    @cache.delete("service-{service_id}")
    def update_service(self, service_id, **kwargs):
        """
        Update a service.
        """
        data = _attach_current_user(kwargs)
        disallowed_attributes = set(data.keys()) - {
            "active",
            "billing_contact_email_addresses",
            "billing_contact_names",
            "billing_reference",
            "consent_to_research",
            "contact_link",
            "created_by",
            "count_as_live",
            "email_from",
            "free_sms_fragment_limit",
            "go_live_at",
            "go_live_user",
            "message_limit",
            "name",
            "notes",
            "organization_type",
            "permissions",
            "prefix_sms",
            "purchase_order_number",
            "rate_limit",
            "reply_to_email_address",
            ServicePermission.RESEARCH_MODE,
            "restricted",
            "sms_sender",
            "volume_email",
            "volume_sms",
        }
        if disallowed_attributes:
            raise TypeError(
                "Not allowed to update service attributes: {}".format(
                    ", ".join(disallowed_attributes)
                )
            )

        endpoint = "/service/{0}".format(service_id)
        return self.post(endpoint, data)

    @cache.delete("live-service-and-organization-counts")
    def update_status(self, service_id, live):
        try:
            return self.update_service(
                service_id,
                message_limit=250000 if live else 50,
                restricted=(not live),
                go_live_at=str(datetime.utcnow()) if live else None,
            )
        except Exception as e:
            current_app.logger.error(f"Error updating status {str(e)}", exc_info=True)
            raise e

    @cache.delete("live-service-and-organization-counts")
    def update_count_as_live(self, service_id, count_as_live):
        try:
            return self.update_service(
                service_id,
                count_as_live=count_as_live,
            )
        except Exception as e:
            current_app.logger.error(
                f"Error updating count as live {str(e)}", exc_info=True
            )
            raise e

    # This method is not cached because it calls through to one which is
    def update_service_with_properties(self, service_id, properties):
        return self.update_service(service_id, **properties)

    @cache.delete("service-{service_id}")
    @cache.delete("service-{service_id}-templates")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def archive_service(self, service_id, cached_service_user_ids):
        if cached_service_user_ids:
            redis_client.delete(*map("user-{}".format, cached_service_user_ids))
        return self.post("/service/{}/archive".format(service_id), data=None)

    @cache.delete("service-{service_id}")
    def suspend_service(self, service_id):
        return self.post("/service/{}/suspend".format(service_id), data=None)

    @cache.delete("service-{service_id}")
    def resume_service(self, service_id):
        return self.post("/service/{}/resume".format(service_id), data=None)

    @cache.delete("service-{service_id}")
    @cache.delete("user-{user_id}")
    def remove_user_from_service(self, service_id, user_id):
        """
        Remove a user from a service
        """
        endpoint = "/service/{service_id}/users/{user_id}".format(
            service_id=service_id, user_id=user_id
        )
        data = _attach_current_user({})
        return self.delete(endpoint, data)

    @cache.delete("service-{service_id}-templates")
    def create_service_template(
        self, name, type_, content, service_id, subject=None, parent_folder_id=None
    ):
        """
        Create a service template.
        """
        data = {
            "name": name,
            "template_type": type_,
            "content": content,
            "service": service_id,
            "process_type": "normal",
        }
        if subject:
            data.update({"subject": subject})
        if parent_folder_id:
            data.update({"parent_folder_id": parent_folder_id})
        data = _attach_current_user(data)
        endpoint = "/service/{0}/template".format(service_id)
        return self.post(endpoint, data)

    @cache.delete("service-{service_id}-templates")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def update_service_template(
        self, id_, name, type_, content, service_id, subject=None
    ):
        """
        Update a service template.
        """
        data = {
            "id": id_,
            "name": name,
            "template_type": type_,
            "content": content,
            "service": service_id,
        }
        if subject:
            data.update({"subject": subject})
        data.update({"process_type": "normal"})
        data = _attach_current_user(data)
        endpoint = "/service/{0}/template/{1}".format(service_id, id_)
        return self.post(endpoint, data)

    @cache.delete("service-{service_id}-templates")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def redact_service_template(self, service_id, id_):
        return self.post(
            "/service/{}/template/{}".format(service_id, id_),
            _attach_current_user({"redact_personalisation": True}),
        )

    @cache.delete("service-{service_id}-templates")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def update_service_template_sender(self, service_id, template_id, reply_to):
        data = {
            "reply_to": reply_to,
        }
        data = _attach_current_user(data)
        return self.post(
            "/service/{0}/template/{1}".format(service_id, template_id), data
        )

    @cache.set("service-{service_id}-template-{template_id}-version-{version}")
    def get_service_template(self, service_id, template_id, version=None):
        """
        Retrieve a service template.
        """
        endpoint = "/service/{service_id}/template/{template_id}".format(
            service_id=service_id, template_id=template_id
        )
        if version:
            endpoint = "{base}/version/{version}".format(base=endpoint, version=version)
        return self.get(endpoint)

    @cache.set("service-{service_id}-template-{template_id}-versions")
    def get_service_template_versions(self, service_id, template_id):
        """
        Retrieve a list of versions for a template
        """
        endpoint = "/service/{service_id}/template/{template_id}/versions".format(
            service_id=service_id, template_id=template_id
        )
        return self.get(endpoint)

    def get_precompiled_template(self, service_id):
        """
        Returns the precompiled template for a service, creating it if it doesn't already exist
        """
        return self.get("/service/{}/template/precompiled".format(service_id))

    @cache.set("service-{service_id}-templates")
    def get_service_templates(self, service_id):
        """
        Retrieve all templates for service.
        """
        endpoint = "/service/{service_id}/template?detailed=False".format(
            service_id=service_id
        )
        return self.get(endpoint)

    # This doesn’t need caching because it calls through to a method which is cached
    def count_service_templates(self, service_id, template_type=None):
        return len(
            [
                template
                for template in self.get_service_templates(service_id)["data"]
                if (not template_type or template["template_type"] == template_type)
            ]
        )

    @cache.delete("service-{service_id}-templates")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def delete_service_template(self, service_id, template_id):
        """
        Set a service template's archived flag to True
        """
        endpoint = "/service/{0}/template/{1}".format(service_id, template_id)
        data = {"archived": True}
        data = _attach_current_user(data)
        return self.post(endpoint, data=data)

    # Temp access of service history data. Includes service and api key history
    def get_service_history(self, service_id):
        return self.get("/service/{0}/history".format(service_id))["data"]

    def get_service_service_history(self, service_id):
        return self.get_service_history(service_id)["service_history"]

    def get_service_api_key_history(self, service_id):
        return self.get_service_history(service_id)["api_key_history"]

    def get_monthly_notification_stats(self, service_id, year):
        return self.get(
            url="/service/{}/notifications/monthly?year={}".format(service_id, year)
        )

    def get_guest_list(self, service_id):
        return self.get(url="/service/{}/guest-list".format(service_id))

    @cache.delete("service-{service_id}")
    def update_guest_list(self, service_id, data):
        return self.put(url="/service/{}/guest-list".format(service_id), data=data)

    def get_inbound_sms(self, service_id, user_number=""):
        # POST prevents the user phone number leaking into our logs
        return self.post(
            "/service/{}/inbound-sms".format(
                service_id,
            ),
            data={"phone_number": user_number},
        )

    def get_most_recent_inbound_sms(self, service_id, page=None):
        return self.get(
            "/service/{}/inbound-sms/most-recent".format(
                service_id,
            ),
            params={"page": page},
        )

    def get_inbound_sms_by_id(self, service_id, notification_id):
        return self.get(
            "/service/{}/inbound-sms/{}".format(
                service_id,
                notification_id,
            )
        )

    def get_inbound_sms_summary(self, service_id):
        return self.get("/service/{}/inbound-sms/summary".format(service_id))

    @cache.delete("service-{service_id}")
    def create_service_inbound_api(self, service_id, url, bearer_token, user_id):
        data = {"url": url, "bearer_token": bearer_token, "updated_by_id": user_id}
        return self.post("/service/{}/inbound-api".format(service_id), data)

    @cache.delete("service-{service_id}")
    def update_service_inbound_api(
        self, service_id, url, bearer_token, user_id, inbound_api_id
    ):
        data = {"url": url, "updated_by_id": user_id}
        if bearer_token:
            data["bearer_token"] = bearer_token
        return self.post(
            "/service/{}/inbound-api/{}".format(service_id, inbound_api_id), data
        )

    def get_service_inbound_api(self, service_id, inbound_sms_api_id):
        return self.get(
            "/service/{}/inbound-api/{}".format(service_id, inbound_sms_api_id)
        )["data"]

    @cache.delete("service-{service_id}")
    def delete_service_inbound_api(self, service_id, callback_api_id):
        return self.delete(
            "/service/{}/inbound-api/{}".format(service_id, callback_api_id)
        )

    def get_reply_to_email_addresses(self, service_id):
        return self.get("/service/{}/email-reply-to".format(service_id))

    def get_reply_to_email_address(self, service_id, reply_to_email_id):
        return self.get(
            "/service/{}/email-reply-to/{}".format(service_id, reply_to_email_id)
        )

    def verify_reply_to_email_address(self, service_id, email_address):
        return self.post(
            "/service/{}/email-reply-to/verify".format(service_id),
            data={"email": email_address},
        )

    @cache.delete("service-{service_id}")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def add_reply_to_email_address(self, service_id, email_address, is_default=False):
        return self.post(
            "/service/{}/email-reply-to".format(service_id),
            data={"email_address": email_address, "is_default": is_default},
        )

    @cache.delete("service-{service_id}")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def update_reply_to_email_address(
        self, service_id, reply_to_email_id, email_address, is_default=False
    ):
        return self.post(
            "/service/{}/email-reply-to/{}".format(
                service_id,
                reply_to_email_id,
            ),
            data={"email_address": email_address, "is_default": is_default},
        )

    @cache.delete("service-{service_id}")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def delete_reply_to_email_address(self, service_id, reply_to_email_id):
        return self.post(
            "/service/{}/email-reply-to/{}/archive".format(
                service_id, reply_to_email_id
            ),
            data=None,
        )

    def get_sms_senders(self, service_id):
        return self.get("/service/{}/sms-sender".format(service_id))

    def get_sms_sender(self, service_id, sms_sender_id):
        return self.get("/service/{}/sms-sender/{}".format(service_id, sms_sender_id))

    @cache.delete("service-{service_id}")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def add_sms_sender(
        self, service_id, sms_sender, is_default=False, inbound_number_id=None
    ):
        data = {"sms_sender": sms_sender, "is_default": is_default}
        if inbound_number_id:
            data["inbound_number_id"] = inbound_number_id
        return self.post("/service/{}/sms-sender".format(service_id), data=data)

    @cache.delete("service-{service_id}")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def update_sms_sender(
        self, service_id, sms_sender_id, sms_sender, is_default=False
    ):
        return self.post(
            "/service/{}/sms-sender/{}".format(service_id, sms_sender_id),
            data={"sms_sender": sms_sender, "is_default": is_default},
        )

    @cache.delete("service-{service_id}")
    @cache.delete_by_pattern("service-{service_id}-template-*")
    def delete_sms_sender(self, service_id, sms_sender_id):
        return self.post(
            "/service/{}/sms-sender/{}/archive".format(service_id, sms_sender_id),
            data=None,
        )

    def get_service_callback_api(self, service_id, callback_api_id):
        return self.get(
            "/service/{}/delivery-receipt-api/{}".format(service_id, callback_api_id)
        )["data"]

    @cache.delete("service-{service_id}")
    def update_service_callback_api(
        self, service_id, url, bearer_token, user_id, callback_api_id
    ):
        data = {"url": url, "updated_by_id": user_id}
        if bearer_token:
            data["bearer_token"] = bearer_token
        return self.post(
            "/service/{}/delivery-receipt-api/{}".format(service_id, callback_api_id),
            data,
        )

    @cache.delete("service-{service_id}")
    def delete_service_callback_api(self, service_id, callback_api_id):
        return self.delete(
            "/service/{}/delivery-receipt-api/{}".format(service_id, callback_api_id)
        )

    @cache.delete("service-{service_id}")
    def create_service_callback_api(self, service_id, url, bearer_token, user_id):
        data = {"url": url, "bearer_token": bearer_token, "updated_by_id": user_id}
        return self.post("/service/{}/delivery-receipt-api".format(service_id), data)

    @cache.delete("service-{service_id}-data-retention")
    def create_service_data_retention(
        self, service_id, notification_type, days_of_retention
    ):
        data = {
            "notification_type": notification_type,
            "days_of_retention": days_of_retention,
        }

        return self.post("/service/{}/data-retention".format(service_id), data)

    @cache.delete("service-{service_id}-data-retention")
    def update_service_data_retention(
        self, service_id, data_retention_id, days_of_retention
    ):
        data = {"days_of_retention": days_of_retention}
        return self.post(
            "/service/{}/data-retention/{}".format(service_id, data_retention_id), data
        )

    @cache.set("service-{service_id}-data-retention")
    def get_service_data_retention(self, service_id):
        return self.get("/service/{}/data-retention".format(service_id))

    def get_notification_count(self, service_id):
        count = 0

        return int(count)

    def get_global_notification_count(self, service_id):
        notification_count = redis_client.get(f"notification-count-{service_id}")
        if notification_count is not None:
            return json.loads(notification_count.decode("utf-8"))

        notification_count = self.get(
            "/service/{}/notification-count".format(service_id)
        )
        redis_client.set(
            f"notification-count-{service_id}", json.dumps(notification_count), ex=30
        )

        return notification_count

    def get_service_invite_data(self, redis_key):
        """
        Retrieve service invite_data.
        """
        return self.get("/service/invite/redis/{0}".format(redis_key))

    def get_service_message_ratio(self, service_id):
        return self.get(
            url="service/get-service-message-ratio?service_id={0}".format(service_id),
        )


service_api_client = ServiceAPIClient()


# TODO, if we try to call get_service_invite_data directly
# from verify, app complains the method is not defined
# If we wrap it like this, the app can find it.
def retrieve_service_invite_data(redis_key):
    return service_api_client.get_service_invite_data(redis_key)
