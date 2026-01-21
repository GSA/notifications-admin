import json
import os


class CloudfoundryConfig:
    def __init__(self):
        self.parsed_services = json.loads(os.environ.get("VCAP_SERVICES") or "{}")
        buckets = self.parsed_services.get("s3") or []
        self.s3_buckets = {bucket["name"]: bucket["credentials"] for bucket in buckets}
        self._empty_bucket_credentials = {
            "bucket": "",
            "access_key_id": "",
            "secret_access_key": "",  # nosec B105 - empty default, not a real password
            "region": "",
        }

    @property
    def redis_url(self):
        try:
            return self.parsed_services["aws-elasticache-redis"][0]["credentials"][
                "uri"
            ]
        except KeyError:
            return os.environ.get("REDIS_URL")

    def s3_credentials(self, service_name):
        return self.s3_buckets.get(service_name) or self._empty_bucket_credentials


cloud_config = CloudfoundryConfig()
