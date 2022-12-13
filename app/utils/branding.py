from app.models.organisation import Organisation

NHS_EMAIL_BRANDING_ID = 'a7dc4e56-660b-4db7-8cff-12c37b12b5ea'


def get_email_choices(service):
    organisation_branding_id = service.organisation.email_branding_id if service.organisation else None

    if (
        service.organisation_type == Organisation.TYPE_FEDERAL
        and service.email_branding_id is not None  # GOV.UK is not current branding
        and organisation_branding_id is None  # no default to supersede it (GOV.UK)
    ):
        yield ('govuk', 'GOV.UK')

    if (
        service.organisation_type == Organisation.TYPE_FEDERAL
        and service.organisation
        and organisation_branding_id is None  # don't offer both if org has default
        and service.email_branding_name.lower() != f'GOV.UK and {service.organisation.name}'.lower()
    ):
        yield ('govuk_and_org', f'GOV.UK and {service.organisation.name}')
