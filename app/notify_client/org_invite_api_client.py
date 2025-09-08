import json
import secrets
from urllib.parse import unquote

from flask import current_app, request

from app import redis_client
from app.enums import InvitedOrgUserStatus
from app.notify_client import NotifyAdminAPIClient, _attach_current_user
from app.utils import hilite
from notifications_utils.url_safe_token import generate_token


class OrgInviteApiClient(NotifyAdminAPIClient):
    def init_app(self, app):
        super().init_app(app)

        self.admin_url = app.config["ADMIN_BASE_URL"]

    def create_invite(self, invite_from_id, org_id, email_address):
        data = {
            "email_address": email_address,
            "invited_by": invite_from_id,
            "invite_link_host": self.admin_url,
        }
        data = _attach_current_user(data)

        ttl = 24 * 60 * 60
        # make and store the state
        state = generate_token(
            str(request.remote_addr),
            current_app.config["SECRET_KEY"],
            current_app.config["DANGEROUS_SALT"],
        )
        state_key = f"login-state-{unquote(state)}"
        redis_client.set(state_key, state, ex=ttl)
        current_app.logger.debug(
            hilite(f"SET THE STATE KEY TO {state} with state_key {state_key}")
        )

        # make and store the nonce
        nonce = secrets.token_urlsafe()
        nonce_key = f"login-nonce-{unquote(nonce)}"
        redis_client.set(nonce_key, nonce, ex=ttl)  # save the nonce to redis.
        current_app.logger.debug(
            hilite(f"SET THE STATE KEY TO {state} with state_key {state_key}")
        )

        data["nonce"] = nonce  # This is passed to api for the invite url.
        data["state"] = state  # This is passed to api for the invite url.

        resp = self.post(url="/organization/{}/invite".format(org_id), data=data)
        current_app.logger.debug(hilite(f"RESP is {resp}"))

        invite_data_key = f"invitedata-{unquote(state)}"
        redis_invite_data = resp["invite"]
        redis_invite_data = json.dumps(redis_invite_data)
        redis_client.set(invite_data_key, redis_invite_data, ex=ttl)
        current_app.logger.debug(
            hilite(f"SET invite_data_key {invite_data_key} to {redis_invite_data}")
        )

        return resp["data"]

    def get_invites_for_organization(self, org_id):
        endpoint = "/organization/{}/invite".format(org_id)
        resp = self.get(endpoint)
        return resp["data"]

    def get_invited_user_for_org(self, org_id, invited_org_user_id):
        return self.get(f"/organization/{org_id}/invite/{invited_org_user_id}")["data"]

    def get_invited_user(self, invited_user_id):
        return self.get(f"/invite/organization/{invited_user_id}")["data"]

    def check_token(self, token):
        resp = self.get(url="/invite/organization/check/{}".format(token))
        return resp["data"]

    def cancel_invited_user(self, org_id, invited_user_id):
        data = {"status": InvitedOrgUserStatus.CANCELLED}
        data = _attach_current_user(data)
        self.post(
            url="/organization/{0}/invite/{1}".format(org_id, invited_user_id),
            data=data,
        )

    def accept_invite(self, org_id, invited_user_id):
        data = {"status": InvitedOrgUserStatus.ACCEPTED}
        self.post(
            url="/organization/{0}/invite/{1}".format(org_id, invited_user_id),
            data=data,
        )


org_invite_api_client = OrgInviteApiClient()
