from itertools import chain

from flask import request


class Navigation:
    mapping = {}
    selected_class = "usa-current"

    def __init__(self):
        self.mapping = {
            navigation: {
                # if not specified, assume endpoints are all in the `main` blueprint.
                self.get_endpoint_with_blueprint(endpoint)
                for endpoint in endpoints
            }
            for navigation, endpoints in self.mapping.items()
        }

    @property
    def endpoints_with_navigation(self):
        return tuple(
            chain.from_iterable(
                (endpoints for navigation_item, endpoints in self.mapping.items())
            )
        )

    def is_selected(self, navigation_item):
        if request.endpoint in self.mapping[navigation_item]:
            return self.selected_class
        return ""

    @staticmethod
    def get_endpoint_with_blueprint(endpoint):
        return endpoint if "." in endpoint else "main.{}".format(endpoint)


class HeaderNavigation(Navigation):
    mapping = {
        "support": {
            "bat_phone",
            "feedback",
            "support",
            "support_public",
            "thanks",
            "triage",
        },
        "features": {
            "features",
            "features_email",
            "features_sms",
            "roadmap",
            "security",
            "terms",
        },
        "using_notify": {
            "get_started",
            "using_notify",
            "pricing",
            "trial_mode_new",
            "message_status",
            "guidance_index",
        },
        "accounts-or-dashboard": {
        },
        "pricing": {
            "how_to_pay",
            "billing_details",
        },
        "documentation": {
            "documentation",
            "integration_testing",
        },
        "user-profile": {
            "user_profile",
            "user_profile_confirm_delete_mobile_number",
            "user_profile_email",
            "user_profile_email_authenticate",
            "user_profile_email_confirm",
            "user_profile_mobile_number",
            "user_profile_mobile_number_authenticate",
            "user_profile_mobile_number_confirm",
            "user_profile_mobile_number_delete",
            "user_profile_name",
            "user_profile_password",
            "user_profile_disable_platform_admin_view",
        },
        "platform-admin": {
            "archive_user",
            "change_user_auth",
            "clear_cache",
            "create_email_branding",
            "edit_sms_provider_ratio",
            "email_branding",
            "find_services_by_name",
            "find_users_by_email",
            "live_services",
            "live_services_csv",
            "notifications_sent_by_service",
            "get_billing_report",
            "get_users_report",
            "get_daily_volumes",
            "get_daily_sms_provider_volumes",
            "get_volumes_by_service",
            "organizations",
            "platform_admin",
            "platform_admin_list_complaints",
            "platform_admin_reports",
            "platform_admin_splash_page",
            "suspend_service",
            "trial_services",
            "update_email_branding",
            "user_information",
            "view_provider",
            "view_providers",
        },
        "sign-in": {
            "revalidate_email_sent",
            "sign_in",
            "two_factor_sms",
            "two_factor_email",
            "two_factor_email_sent",
            "two_factor_email_interstitial",
            "verify",
            "verify_email",
        },
    }

    # header HTML now comes from GOVUK Frontend so requires a boolean, not an attribute
    def is_selected(self, navigation_item):
        return request.endpoint in self.mapping[navigation_item]


class MainNavigation(Navigation):
    mapping = {
        "dashboard": {
            "conversation",
            "inbox",
            "monthly",
            "service_dashboard",
            "template_usage",
            "view_notification",
            "view_notifications",
        },
        "templates": {
            "action_blocked",
            "add_service_template",
            "check_messages",
            "check_notification",
            "choose_template",
            "choose_template_to_copy",
            "confirm_redact_template",
            "conversation_reply",
            "copy_template",
            "delete_service_template",
            "edit_service_template",
            "manage_template_folder",
            "send_messages",
            "send_one_off",
            "send_one_off_step",
            "send_one_off_to_myself",
            "set_sender",
            "set_template_sender",
            "view_template",
            "view_template_version",
            "view_template_versions",
        },
        "uploads": {
            "uploads",
            "view_job",
            "view_jobs",
        },
        "team-members": {
            "confirm_edit_user_email",
            "confirm_edit_user_mobile_number",
            "edit_user_email",
            "edit_user_mobile_number",
            "edit_user_permissions",
            "invite_user",
            "manage_users",
            "remove_user_from_service",
        },
        "usage": {
            "usage",
        },
        "settings": {
            # 'add_organization_from_gp_service',
            "email_branding_govuk",
            "email_branding_govuk_and_org",
            "email_branding_organization",
            "email_branding_request",
            "email_branding_something_else",
            "estimate_usage",
            "link_service_to_organization",
            "request_to_go_live",
            "service_add_email_reply_to",
            "service_add_sms_sender",
            "service_confirm_delete_email_reply_to",
            "service_confirm_delete_sms_sender",
            "service_edit_email_reply_to",
            "service_edit_sms_sender",
            "service_email_reply_to",
            "service_name_change",
            "service_preview_email_branding",
            "service_set_auth_type",
            "service_set_channel",
            "send_files_by_email_contact_details",
            "service_set_email_branding",
            "service_set_inbound_number",
            "service_set_inbound_sms",
            "service_set_international_sms",
            "service_set_reply_to_email",
            "service_set_sms_prefix",
            "service_verify_reply_to_address",
            "service_verify_reply_to_address_updates",
            "service_settings",
            "service_sms_senders",
            "set_free_sms_allowance",
            "set_message_limit",
            "set_rate_limit",
            "submit_request_to_go_live",
        },
        "api-integration": {
            "api_callbacks",
            "api_documentation",
            "api_integration",
            "api_keys",
            "create_api_key",
            "delivery_status_callback",
            "received_text_messages_callback",
            "revoke_api_key",
            "guest_list",
            "old_guest_list",
        },
    }


class CaseworkNavigation(Navigation):
    mapping = {
        "send-one-off": {
            "choose_template",
            "send_one_off",
            "send_one_off_step",
            "send_one_off_to_myself",
        },
        "sent-messages": {
            "view_notifications",
            "view_notification",
        },
        "uploads": {
            "view_jobs",
            "view_job",
            "uploads",
        },
    }


class OrgNavigation(Navigation):
    mapping = {
        "dashboard": {
            "organization_dashboard",
        },
        "settings": {
            "edit_organization_billing_details",
            "edit_organization_domains",
            "edit_organization_email_branding",
            "edit_organization_go_live_notes",
            "edit_organization_name",
            "edit_organization_notes",
            "edit_organization_type",
            "organization_preview_email_branding",
            "organization_settings",
        },
        "team-members": {
            "edit_organization_user",
            "invite_org_user",
            "manage_org_users",
            "remove_user_from_organization",
        },
        "trial-services": {
            "organization_trial_mode_services",
        },
        "billing": {
            "organization_billing",
        },
    }
