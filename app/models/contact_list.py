from functools import partial
from os import path
from uuid import uuid4

from flask import abort, current_app
from notifications_utils.formatters import strip_all_whitespace
from notifications_utils.recipients import RecipientCSV
from notifications_utils.s3 import s3upload as utils_s3upload
from werkzeug.utils import cached_property

from app.models import JSONModel, ModelList
from app.models.job import PaginatedJobsAndScheduledJobs
from app.notify_client.contact_list_api_client import contact_list_api_client
from app.s3_client import (
    get_s3_contents,
    get_s3_metadata,
    get_s3_object,
    set_s3_metadata,
)
from app.s3_client.s3_csv_client import s3upload, set_metadata_on_csv_upload
from app.utils.templates import get_sample_template


class ContactList(JSONModel):

    ALLOWED_PROPERTIES = {
        'id',
        'created_at',
        'created_by',
        'has_jobs',
        'recent_job_count',
        'service_id',
        'original_file_name',
        'row_count',
        'template_type',
    }

    upload_type = 'contact_list'

    @classmethod
    def from_id(cls, contact_list_id, *, service_id):
        return cls(contact_list_api_client.get_contact_list(
            service_id=service_id,
            contact_list_id=contact_list_id,
        ))

    @staticmethod
    def get_bucket_credentials(key):
        return current_app.config['CONTACT_LIST_BUCKET'][key]

    @staticmethod
    def get_bucket_name():
        return ContactList.get_bucket_credentials('bucket')

    @staticmethod
    def get_access_key():
        return ContactList.get_bucket_credentials('access_key_id')

    @staticmethod
    def get_secret_key():
        return ContactList.get_bucket_credentials('secret_access_key')

    @staticmethod
    def get_region():
        return ContactList.get_bucket_credentials('region')

    @staticmethod
    def get_filename(service_id, upload_id):
        return f"service-{service_id}-notify/{upload_id}.csv"

    @staticmethod
    def get_s3_arguments(service_id, upload_id):
        return (
            ContactList.get_bucket_name(),
            ContactList.get_filename(service_id, upload_id),
            ContactList.get_access_key(),
            ContactList.get_secret_key(),
            ContactList.get_region(),
        )

    @staticmethod
    def upload(service_id, file_dict):
        upload_id = str(uuid4())
        utils_s3upload(
            filedata=file_dict['data'],
            region=ContactList.get_region(),
            bucket_name=ContactList.get_bucket_name(),
            file_location=ContactList.get_filename(service_id, upload_id),
            access_key=ContactList.get_access_key(),
            secret_key=ContactList.get_secret_key(),
        )
        return upload_id

    @staticmethod
    def download(service_id, upload_id):
        return strip_all_whitespace(
            get_s3_contents(
                get_s3_object(*ContactList.get_s3_arguments(service_id, upload_id))))

    @staticmethod
    def set_metadata(service_id, upload_id, **kwargs):
        return set_s3_metadata(get_s3_object(*ContactList.get_s3_arguments(service_id, upload_id)), **kwargs)

    @staticmethod
    def get_metadata(service_id, upload_id):
        return get_s3_metadata(get_s3_object(*ContactList.get_s3_arguments(service_id, upload_id)))

    def copy_to_uploads(self):
        raise RuntimeError("RCA probably an issue with copying between buckets")
        metadata = self.get_metadata(self.service_id, self.id)
        new_upload_id = s3upload(
            self.service_id,
            {'data': self.contents},
            ContactList.get_region(),
        )
        set_metadata_on_csv_upload(
            self.service_id,
            new_upload_id,
            **metadata,
        )
        return new_upload_id

    @classmethod
    def create(cls, service_id, upload_id):

        metadata = cls.get_metadata(service_id, upload_id)

        if not metadata.get('valid'):
            abort(403)

        return cls(contact_list_api_client.create_contact_list(
            service_id=service_id,
            upload_id=upload_id,
            original_file_name=metadata['original_file_name'],
            row_count=int(metadata['row_count']),
            template_type=metadata['template_type'],
        ))

    def delete(self):
        contact_list_api_client.delete_contact_list(
            service_id=self.service_id,
            contact_list_id=self.id,
        )

    @property
    def contents(self):
        return self.download(self.service_id, self.id)

    @cached_property
    def recipients(self):
        return RecipientCSV(
            self.contents,
            template=get_sample_template(self.template_type),
            allow_international_sms=True,
            max_initial_rows_shown=50,
        )

    @property
    def saved_file_name(self):
        file_name, extention = path.splitext(self.original_file_name)
        return f'{file_name}.csv'

    def get_jobs(self, *, page, limit_days=None):
        return PaginatedJobsAndScheduledJobs(
            self.service_id,
            contact_list_id=self.id,
            page=page,
            limit_days=limit_days,
        )


class ContactLists(ModelList):

    client_method = contact_list_api_client.get_contact_lists
    model = ContactList
    sort_function = partial(
        sorted,
        key=lambda item: item['created_at'],
        reverse=True,
    )

    def __init__(self, service_id, template_type=None):
        super().__init__(service_id)
        self.items = self.sort_function([
            item for item in self.items
            if template_type in {item['template_type'], None}
        ])


class ContactListsAlphabetical(ContactLists):

    sort_function = partial(
        sorted,
        key=lambda item: item['original_file_name'].lower(),
    )
