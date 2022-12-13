from notifications_utils.clients.redis.redis_client import RedisClient
from notifications_utils.clients.zendesk.zendesk_client import ZendeskClient

zendesk_client = ZendeskClient()
redis_client = RedisClient()
