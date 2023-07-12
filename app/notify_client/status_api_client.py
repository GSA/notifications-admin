from app.notify_client import NotifyAdminAPIClient, cache


class StatusApiClient(NotifyAdminAPIClient):

    def get_status(self, *params):
        return self.get(url='/_status', *params)

    @cache.set('live-service-and-organization-counts', ttl_in_seconds=3600)
    def get_count_of_live_services_and_organizations(self):
        return self.get(url='/_status/live-service-and-organization-counts')

    @cache.set('live-service-and-organization-counts', ttl_in_seconds=3600)
    def get_count_of_live_services_and_organizations_cached(self):
        return self.get(url='/_status/live-service-and-organization-counts')


status_api_client = StatusApiClient()
