from collections import OrderedDict

from werkzeug.utils import cached_property

from app.models import JSONModel, ModelList, SerialisedModelCollection, SortByNameMixin
from app.notify_client.organizations_api_client import organizations_client


class Organization(JSONModel, SortByNameMixin):
    TYPE_FEDERAL = "federal"
    TYPE_STATE = "state"
    TYPE_OTHER = "other"

    TYPE_LABELS = OrderedDict(
        [
            (TYPE_FEDERAL, "Federal government"),
            (TYPE_STATE, "State government"),
            (TYPE_OTHER, "Other"),
        ]
    )

    ALLOWED_PROPERTIES = {
        "id",
        "name",
        "active",
        "organization_type",
        "domains",
        "count_of_live_services",
        "billing_contact_email_addresses",
        "billing_contact_names",
        "billing_reference",
        "purchase_order_number",
        "notes",
    }

    @classmethod
    def from_id(cls, org_id):
        if not org_id:
            return cls({})
        return cls(organizations_client.get_organization(org_id))

    @classmethod
    def from_domain(cls, domain):
        return cls(organizations_client.get_organization_by_domain(domain))

    @classmethod
    def from_service(cls, service_id):
        return cls(organizations_client.get_service_organization(service_id))

    @classmethod
    def create_from_form(cls, form):
        return cls.create(
            name=form.name.data,
            organization_type=form.organization_type.data,
        )

    @classmethod
    def create(cls, name, organization_type):
        return cls(
            organizations_client.create_organization(
                name=name,
                organization_type=organization_type,
            )
        )

    def __init__(self, _dict):
        super().__init__(_dict)

        if self._dict == {}:
            self.name = None
            self.domains = []
            self.organization_type = None

    @property
    def organization_type_label(self):
        return self.TYPE_LABELS.get(self.organization_type)

    @property
    def billing_details(self):
        billing_details = [
            self.billing_contact_email_addresses,
            self.billing_contact_names,
            self.billing_reference,
            self.purchase_order_number,
        ]
        if any(billing_details):
            return billing_details
        else:
            return None

    @cached_property
    def services(self):
        return organizations_client.get_organization_services(self.id)

    @cached_property
    def service_ids(self):
        return [s["id"] for s in self.services]

    @property
    def live_services(self):
        return [s for s in self.services if s["active"] and not s["restricted"]]

    @property
    def trial_services(self):
        return [s for s in self.services if not s["active"] or s["restricted"]]

    @cached_property
    def invited_users(self):
        from app.models.user import OrganizationInvitedUsers

        return OrganizationInvitedUsers(self.id)

    @cached_property
    def active_users(self):
        from app.models.user import OrganizationUsers

        return OrganizationUsers(self.id)

    @cached_property
    def team_members(self):
        return sorted(
            self.invited_users + self.active_users,
            key=lambda user: user.email_address.lower(),
        )

    def update(self, delete_services_cache=False, **kwargs):
        response = organizations_client.update_organization(
            self.id,
            cached_service_ids=self.service_ids if delete_services_cache else None,
            **kwargs
        )
        self.__init__(response)

    def associate_service(self, service_id):
        organizations_client.update_service_organization(service_id, self.id)

    def services_and_usage(self, financial_year):
        return organizations_client.get_services_and_usage(self.id, financial_year)


class Organizations(SerialisedModelCollection):
    model = Organization


class AllOrganizations(ModelList, Organizations):
    client_method = organizations_client.get_organizations
