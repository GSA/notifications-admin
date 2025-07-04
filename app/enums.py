from enum import Enum


class NotificationStatus(Enum):
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


class ApiKeyType(Enum):
    NORMAL = "normal"
    TEAM = "team"
    TEST = "test"


class JobStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in progress"
    FINISHED = "finished"
    SENDING_LIMITS_EXCEEDED = "sending limits exceeded"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    READY_TO_SEND = "ready to send"
    SENT_TO_DVLA = "sent to dvla"


class InvitedUserStatus(Enum):
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class InvitedOrgUserStatus(Enum):
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"


class VerificationStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"


class HealthStatus(Enum):
    OK = "ok"
    ERROR = "error"


class AuthType(Enum):
    EMAIL_AUTH = "email_auth"
    SMS_AUTH = "sms_auth"


# TODO: UserRole enum
# class UserRole(Enum):
#     ADMIN = "admin"
#     USER = "user"
#     GUEST = "guest"


# TODO: NotificationType enum
# class NotificationType(Enum):
#     EMAIL = "email"
#     SMS = "sms"
#     PUSH = "push"
