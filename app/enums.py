from enum import StrEnum


class NotificationStatus(StrEnum):
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
