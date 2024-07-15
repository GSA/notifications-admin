import os

from flask import abort, has_request_context, request
from flask_login import current_user
from notifications_python_client import __version__
from notifications_python_client.base import BaseAPIClient

from app.extensions import redis_client
from notifications_utils.clients.redis import RequestCache

cache = RequestCache(redis_client)


def _attach_current_user(data):
    return dict(created_by=current_user.id, **data)


class NotifyAdminAPIClient(BaseAPIClient):
    def __init__(self):
        super().__init__("a" * 73, "b")

    def init_app(self, app):
        self.base_url = app.config["API_HOST_NAME"]
        self.service_id = app.config["ADMIN_CLIENT_USER_NAME"]
        self.api_key = app.config["ADMIN_CLIENT_SECRET"]
        self.route_secret = app.config["ROUTE_SECRET_KEY_1"]

    def generate_headers(self, api_token):
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer {}".format(api_token),
            "X-Custom-Forwarder": self.route_secret,
            "User-agent": "NOTIFY-API-PYTHON-CLIENT/{}".format(__version__),
        }
        return self._add_request_id_header(headers)

    @staticmethod
    def _add_request_id_header(headers):
        if not has_request_context():
            return headers
        headers["X-B3-TraceId"] = request.request_id
        headers["X-B3-SpanId"] = request.span_id
        return headers

    def check_inactive_service(self):
        # this file is imported in app/__init__.py before current_service is initialised, so need to import later
        # to prevent cyclical imports
        from app import current_service

        # if the current service is inactive and the user isn't a platform admin, we should block them from making any
        # stateful modifications to that service
        if (
            current_service
            and not current_service.active
            and not current_user.platform_admin
        ):
            abort(403)

    def check_inactive_user(self, *args):
        still_signing_in = False
        for arg in args:
            arg = str(arg)
            if "get-login-gov-user" in arg or "user/email" in arg or "/activate" or "/email-code" in arg:
                still_signing_in = True
        # TODO:  Update this once E2E tests are managed by a feature flag or some other main config option.
        if os.getenv("NOTIFY_E2E_TEST_EMAIL"):
            # allow end-to-end tests to skip check
            pass
        elif still_signing_in is True:
            # we are not full signed in yet
            pass
        elif not current_user or not current_user.is_active:
            abort(403)

    def post(self, *args, **kwargs):
        self.check_inactive_service()
        self.check_inactive_user(args)
        return super().post(*args, **kwargs)

    def put(self, *args, **kwargs):
        self.check_inactive_service()
        self.check_inactive_user()
        return super().put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.check_inactive_service()
        self.check_inactive_user()
        return super().delete(*args, **kwargs)


class InviteTokenError(Exception):
    pass
