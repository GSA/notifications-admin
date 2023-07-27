from itertools import chain

from notifications_python_client.errors import HTTPError

from app.extensions import redis_client
from app.notify_client import NotifyAdminAPIClient, cache


class OrganizationsClient(NotifyAdminAPIClient):

    @cache.set('organizations')
    def get_organizations(self):
        return self.get(url='/organizations')

    @cache.set('domains')
    def get_domains(self):
        return list(chain.from_iterable(
            organization['domains']
            for organization in self.get_organizations()
        ))

    def get_organization(self, org_id):
        return self.get(url='/organizations/{}'.format(org_id))

    @cache.set('organization-{org_id}-name')
    def get_organization_name(self, org_id):
        return self.get_organization(org_id)['name']

    def get_organization_by_domain(self, domain):
        try:
            return self.get(
                url='/organizations/by-domain?domain={}'.format(domain),
            )
        except HTTPError as error:
            if error.status_code == 404:
                return None
            raise error

    @cache.delete('organizations')
    def create_organization(self, name, organization_type):
        return self.post(
            url="/organizations",
            data={
                "name": name,
                "organization_type": organization_type,
            }
        )

    @cache.delete('domains')
    @cache.delete('organizations')
    def update_organization(self, org_id, cached_service_ids=None, **kwargs):
        api_response = self.post(url="/organizations/{}".format(org_id), data=kwargs)

        if cached_service_ids:
            redis_client.delete(*map('service-{}'.format, cached_service_ids))

        if 'name' in kwargs:
            redis_client.delete(f'organization-{org_id}-name')

        return api_response

    @cache.delete('service-{service_id}')
    @cache.delete('live-service-and-organization-counts')
    @cache.delete('organizations')
    def update_service_organization(self, service_id, org_id):
        data = {
            'service_id': service_id
        }
        return self.post(
            url="/organizations/{}/service".format(org_id),
            data=data
        )

    def get_organization_services(self, org_id):
        return self.get(url="/organizations/{}/services".format(org_id))

    @cache.delete('user-{user_id}')
    def remove_user_from_organization(self, org_id, user_id):
        return self.delete(f'/organizations/{org_id}/users/{user_id}')

    def get_services_and_usage(self, org_id, year):
        return self.get(
            url=f"/organizations/{org_id}/services-with-usage",
            params={"year": str(year)}
        )


organizations_client = OrganizationsClient()
