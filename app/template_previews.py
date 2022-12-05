import requests
from flask import current_app

from app import current_service


class TemplatePreview:
    @classmethod
    def from_database_object(cls, template, filetype, values=None, page=None):
        data = {
            'letter_contact_block': template.get('reply_to_text', ''),
            'template': template,
            'values': values,
            'filename': current_service.letter_branding and current_service.letter_branding['filename']
        }
        resp = requests.post(
            '{}/preview.{}{}'.format(
                current_app.config['TEMPLATE_PREVIEW_API_HOST'],
                filetype,
                '?page={}'.format(page) if page else '',
            ),
            json=data,
            headers={'Authorization': 'Token {}'.format(current_app.config['TEMPLATE_PREVIEW_API_KEY'])}
        )
        return (resp.content, resp.status_code, resp.headers.items())

    @classmethod
    def from_example_template(cls, template, filename):
        data = {
            'letter_contact_block': template.get('reply_to_text'),
            'template': template,
            'values': None,
            'filename': filename
        }
        resp = requests.post(
            '{}/preview.png'.format(current_app.config['TEMPLATE_PREVIEW_API_HOST']),
            json=data,
            headers={'Authorization': 'Token {}'.format(current_app.config['TEMPLATE_PREVIEW_API_KEY'])}
        )
        return (resp.content, resp.status_code, resp.headers.items())

    @classmethod
    def from_utils_template(cls, template, filetype, page=None):
        return cls.from_database_object(
            template._template,
            filetype,
            template.values,
            page=page,
        )
