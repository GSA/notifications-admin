from enum import StrEnum


class NotificationStatus(StrEnum):
    REQUESTED = "requested"
    CREATED = "created"
    PENDING = "pending"
    SENDING = "sending"

    DELIVERED = "delivered"
    SENT = "sent"

    FAILED = "failed"
    TEMPORARY_FAILURE = "temporary-failure"
    PERMANENT_FAILURE = "permanent-failure"
    TECHNICAL_FAILURE = "technical-failure"
    VALIDATION_FAILED = "validation-failed"
    CANCELLED = "cancelled"

    @classmethod
    def sending_statuses(cls):
        return [cls.CREATED, cls.PENDING, cls.SENDING]

    @classmethod
    def delivered_statuses(cls):
        return [cls.DELIVERED, cls.SENT]

    @classmethod
    def failure_statuses(cls):
        return [
            cls.FAILED,
            cls.TEMPORARY_FAILURE,
            cls.PERMANENT_FAILURE,
            cls.TECHNICAL_FAILURE,
            cls.VALIDATION_FAILED,
        ]

    @classmethod
    def requested_statuses(cls):
        return (
            cls.sending_statuses() + cls.delivered_statuses() + cls.failure_statuses()
        )


class NotificationType(StrEnum):
    EMAIL = "email"
    SMS = "sms"


class OrganizationType(StrEnum):
    FEDERAL = "federal"
    STATE = "state"
    OTHER = "other"


class ApiKeyType(StrEnum):
    NORMAL = "normal"
    TEAM = "team"
    TEST = "test"


class JobStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in progress"
    FINISHED = "finished"
    SENDING_LIMITS_EXCEEDED = "sending limits exceeded"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    READY_TO_SEND = "ready to send"
    SENT_TO_DVLA = "sent to dvla"


class ServicePermission(StrEnum):
    SEND_MESSAGES = "send_messages"
    MANAGE_SERVICE = "manage_service"
    MANAGE_TEMPLATES = "manage_templates"
    SEND_TEXTS = "send_texts"
    MANAGE_SETTINGS = "manage_settings"
    INBOUND_SMS = "inbound_sms"
    INTERNATIONAL_SMS = "international_sms"
    EMAIL_AUTH = "email_auth"
    EDIT_FOLDER_PERMISSIONS = "edit_folder_permissions"
    RESEARCH_MODE = "research_mode"
    UPLOAD_DOCUMENT = "upload_document"
    VIEW_ACTIVITY = "view_activity"
    MANAGE_USERS = "manage_users"
    SEND_EMAILS = "send_emails"


class InvitedUserStatus(StrEnum):
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class InvitedOrgUserStatus(StrEnum):
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"


class AuthType(StrEnum):
    EMAIL_AUTH = "email_auth"
    SMS_AUTH = "sms_auth"
