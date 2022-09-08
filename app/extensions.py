from notifications_utils.clients.antivirus.antivirus_client import (
    AntivirusClient,
)
from notifications_utils.clients.zendesk.zendesk_client import ZendeskClient

from app.redis_client.redis_client import RedisClient

antivirus_client = AntivirusClient()
zendesk_client = ZendeskClient()
redis_client = RedisClient()
