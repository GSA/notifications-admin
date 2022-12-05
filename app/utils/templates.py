from notifications_utils.template import (
    EmailPreviewTemplate,
    SMSPreviewTemplate,
)


def get_sample_template(template_type):
    if template_type == 'email':
        return EmailPreviewTemplate({'content': 'any', 'subject': '', 'template_type': 'email'})
    if template_type == 'sms':
        return SMSPreviewTemplate({'content': 'any', 'template_type': 'sms'})


def get_template(
    template,
    service,
    show_recipient=False,
    redact_missing_personalisation=False,
    email_reply_to=None,
    sms_sender=None,
):
    if 'email' == template['template_type']:
        return EmailPreviewTemplate(
            template,
            from_name=service.name,
            from_address='{}@notifications.service.gov.uk'.format(service.email_from),
            show_recipient=show_recipient,
            redact_missing_personalisation=redact_missing_personalisation,
            reply_to=email_reply_to,
        )
    if 'sms' == template['template_type']:
        return SMSPreviewTemplate(
            template,
            prefix=service.name,
            show_prefix=service.prefix_sms,
            sender=sms_sender,
            show_sender=bool(sms_sender),
            show_recipient=show_recipient,
            redact_missing_personalisation=redact_missing_personalisation,
        )
