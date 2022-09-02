from notifications_utils.clients.antivirus.antivirus_client import (
    AntivirusClient,
)
from app.redis_client.redis_client import RedisClient
from notifications_utils.clients.zendesk.zendesk_client import ZendeskClient

antivirus_client = AntivirusClient()
zendesk_client = ZendeskClient()
redis_client = RedisClient()
