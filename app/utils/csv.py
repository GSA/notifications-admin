import datetime

import pytz
from flask import current_app
from flask_login import current_user
from notifications_utils.recipients import RecipientCSV

from app.models.spreadsheet import Spreadsheet
from app.utils.templates import get_sample_template


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

    current_app.logger.info("\n\n\n\nENTER generate_notifications_csv")
    if "page" not in kwargs:
        kwargs["page"] = 1

    if kwargs.get("job_id"):
        original_file_contents = s3download(kwargs["service_id"], kwargs["job_id"])
        original_upload = RecipientCSV(
            original_file_contents,
            template=get_sample_template(kwargs["template_type"]),
        )
        original_column_headers = original_upload.column_headers
        fieldnames = [
            "Template",
            "Type",
            "Sent by",
            "Job",
            "Carrier",
            "Carrier Response",
            "Status",
            "Time",
        ]
        for header in original_column_headers:
            fieldnames.append(header)

    else:
        # TODO This is deprecated because everything should be a job now, is it ever invoked?
        fieldnames = [
            "Recipient",
            "Template",
            "Type",
            "Sent by",
            "Job",
            "Carrier",
            "Carrier Response",
            "Status",
            "Time",
        ]
        current_app.logger.warning("Invoking deprecated report format")

    yield ",".join(fieldnames) + "\n"

    while kwargs["page"]:
        notifications_resp = notification_api_client.get_notifications_for_service(
            **kwargs
        )
        for notification in notifications_resp["notifications"]:
            preferred_tz_created_at = convert_report_date_to_preferred_timezone(
                notification["created_at"]
            )

            current_app.logger.info(f"\n\n{notification}")
            if kwargs.get("job_id"):
                values = [
                    notification["template_name"],
                    notification["template_type"],
                    notification["created_by_name"],
                    notification["job_name"],
                    notification["carrier"],
                    notification["provider_response"],
                    notification["status"],
                    preferred_tz_created_at,
                ]
                for header in original_column_headers:
                    values.append(
                        original_upload[notification["row_number"] - 1].get(header).data
                    )

            else:
                # TODO This is deprecated, should not be invoked.  See above
                values = [
                    notification["recipient"],
                    notification["template_name"],
                    notification["template_type"],
                    notification["created_by_name"] or "",
                    notification["job_name"] or "",
                    notification["carrier"],
                    notification["provider_response"],
                    notification["status"],
                    preferred_tz_created_at,
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
    preferred_tz_created_at = preferred_date_obj.strftime("%Y-%m-%d %I:%M:%S %p")

    return f"{preferred_tz_created_at} {get_user_preferred_timezone()}"


def get_user_preferred_timezone():
    if current_user and hasattr(current_user, "preferred_timezone"):
        return current_user.preferred_timezone

    return "US/Eastern"
