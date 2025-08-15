import datetime

import pytz
from flask import current_app, json
from flask_login import current_user

from app.models.spreadsheet import Spreadsheet
from app.utils import hilite
from app.utils.templates import get_sample_template
from notifications_utils.recipients import RecipientCSV


def get_errors_for_csv(recipients, template_type):
    errors = []

    if any(recipients.rows_with_bad_recipients):
        number_of_bad_recipients = len(list(recipients.rows_with_bad_recipients))
        if "sms" == template_type:
            if 1 == number_of_bad_recipients:
                errors.append("fix 1 phone number")
            else:
                errors.append("fix {} phone numbers".format(number_of_bad_recipients))
        elif "email" == template_type:
            if 1 == number_of_bad_recipients:
                errors.append("fix 1 email address")
            else:
                errors.append("fix {} email addresses".format(number_of_bad_recipients))

    if any(recipients.rows_with_missing_data):
        number_of_rows_with_missing_data = len(list(recipients.rows_with_missing_data))
        if 1 == number_of_rows_with_missing_data:
            errors.append("enter missing data in 1 row")
        else:
            errors.append(
                "enter missing data in {} rows".format(number_of_rows_with_missing_data)
            )

    if any(recipients.rows_with_message_too_long):
        number_of_rows_with_message_too_long = len(
            list(recipients.rows_with_message_too_long)
        )
        if 1 == number_of_rows_with_message_too_long:
            errors.append("shorten the message in 1 row")
        else:
            errors.append(
                "shorten the messages in {} rows".format(
                    number_of_rows_with_message_too_long
                )
            )

    if any(recipients.rows_with_empty_message):
        number_of_rows_with_empty_message = len(
            list(recipients.rows_with_empty_message)
        )
        if 1 == number_of_rows_with_empty_message:
            errors.append("check you have content for the empty message in 1 row")
        else:
            errors.append(
                "check you have content for the empty messages in {} rows".format(
                    number_of_rows_with_empty_message
                )
            )

    return errors


def generate_notifications_csv(**kwargs):
    from app import notification_api_client
    from app.s3_client.s3_csv_client import s3download

    if "page" not in kwargs:
        kwargs["page"] = 1

    # This generates the "batch" csv report
    if kwargs.get("job_id"):
        # Some unit tests are mocking the kwargs and turning them into a function instead of dict,
        # hence the try/except.
        try:
            current_app.logger.info(
                hilite(f"Setting up report with kwargs {json.dumps(kwargs)}")
            )
        except TypeError:
            pass

        original_file_contents = s3download(kwargs["service_id"], kwargs["job_id"])
        # This will verify that the user actually did successfully upload a csv for a one-off.  Limit the size
        # we display to 999 characters, because we don't want to show the contents for reports with thousands of rows.
        current_app.logger.info(
            hilite(
                f"Original csv for job_id {kwargs['job_id']}: {original_file_contents[0:999]}"
            )
        )
        original_upload = RecipientCSV(
            original_file_contents,
            template=get_sample_template(kwargs["template_type"]),
        )
        original_column_headers = original_upload.column_headers
        fieldnames = [
            "Phone Number",
            "Template",
            "Sent by",
            "Batch File",
            "Carrier Response",
            "Status",
            "Time",
            "Carrier",
        ]
        for header in original_column_headers:
            if header.lower() != "phone number":
                fieldnames.append(header)

    else:
        # This generates the "full" csv report
        fieldnames = [
            "Phone Number",
            "Template",
            "Sent by",
            "Batch File",
            "Carrier Response",
            "Status",
            "Time",
            "Carrier",
        ]

    yield ",".join(fieldnames) + "\n"

    while kwargs["page"]:
        notifications_resp = notification_api_client.get_notifications_for_service(
            **kwargs
        )
        # Stop if we are finished
        if (
            notifications_resp.get("notifications") is None
            or len(notifications_resp["notifications"]) == 0
        ):
            return

        for notification in notifications_resp["notifications"]:
            preferred_tz_created_at = convert_report_date_to_preferred_timezone(
                notification["created_at"]
            )

            if kwargs.get("job_id"):
                values = [
                    notification["recipient"],
                    notification["template_name"],
                    notification["created_by_name"],
                    notification["job_name"],
                    notification["provider_response"],
                    notification["status"],
                    preferred_tz_created_at,
                    notification["carrier"],
                ]
                for header in original_column_headers:
                    if header.lower() != "phone number":
                        values.append(
                            original_upload[notification["row_number"] - 1]
                            .get(header)
                            .data
                        )

            else:
                values = [
                    notification["recipient"],
                    notification["template_name"],
                    notification["created_by_name"] or "",
                    notification["job_name"] or "",
                    notification["provider_response"],
                    notification["status"],
                    preferred_tz_created_at,
                    notification["carrier"],
                ]
            yield Spreadsheet.from_rows([map(str, values)]).as_csv_data

        if notifications_resp["links"].get("next"):
            kwargs["page"] += 1
        else:
            return
    raise Exception("Should never reach here")


def convert_report_date_to_preferred_timezone(db_date_str_in_utc):
    """
    Report dates in the db are in UTC.  We need to convert them to the user's default timezone,
    which defaults to "US/Eastern"
    """
    date_arr = db_date_str_in_utc.split(" ")
    db_date_str_in_utc = f"{date_arr[0]}T{date_arr[1]}+00:00"
    utc_date_obj = datetime.datetime.fromisoformat(db_date_str_in_utc)

    utc_date_obj = utc_date_obj.astimezone(pytz.utc)
    preferred_timezone = pytz.timezone(get_user_preferred_timezone())
    preferred_date_obj = utc_date_obj.astimezone(preferred_timezone)
    preferred_tz_created_at = preferred_date_obj.strftime("%Y-%m-%d %H:%M:%S")

    return preferred_tz_created_at


def get_user_preferred_timezone():
    if current_user and hasattr(current_user, "preferred_timezone"):
        tz = current_user.preferred_timezone
        # Use a set of common US timezones for quick validation instead of checking all timezones
        valid_timezones = {
            "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
            "US/Alaska", "US/Hawaii", "America/New_York", "America/Chicago",
            "America/Denver", "America/Los_Angeles", "America/Anchorage",
            "America/Honolulu", "America/Phoenix", "America/Puerto_Rico"
        }
        if tz in valid_timezones:
            return tz
    return "US/Eastern"
