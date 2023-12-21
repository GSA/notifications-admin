import app.s3_client.s3_csv_client as s3_csv_client
from app.extensions import RedisClient as redis_client


def add_row_data_to_redis(data, job_id):
    # Take all the data the user upload and assume it is all PII
    # Store a copy of each row to redis
    # As a convenience, because the phone number is what we use the most,
    # store the phone by itself as well so it can be retrieved faster
    rows = data.split("\r\n")
    column_headers = rows[0]
    redis_client.set(f"job_{job_id}_column_headers", column_headers)

    column_list = column_headers.split(",")
    phone_index = 0
    for column in column_list:
        if column == "phone number":
            break
        phone_index = phone_index + 1

    rows.pop(0)
    row_number = 0
    for row in rows:
        row_list = row.split(",")
        redis_client.set(f"job_{job_id}_row_{row_number}", row)
        redis_client.set(
            f"job_{job_id}_row_{row_number}_phone_number", row_list[phone_index]
        )
        row_number = row_number + 1


def get_phone_number(job_id, row_number):
    # convenience method because 99.99% of the time the phone number is all we want
    return redis_client.get(f"job_{job_id}_row_{row_number}_phone_number")


def get_csv_column_headers(job_id):
    return redis_client.get(f"job_{job_id}_column_headers")


def get_csv_row(job_id, row_number):
    # In the event we need to return all csv data for a given row
    # we try to return it in a useful form where we know what the data represents
    # ie {"phone number": "15555555555", "address": "1600 Pennsylvania Avenue"} etc.
    column_headers = get_csv_column_headers(job_id)
    row = redis_client.get(f"job_{job_id}_row_{row_number}")
    columns = column_headers.split(",")
    row_list = row.split(",")
    row_dict = {}
    index = 0
    for column in columns:
        row_dict[column] = row_list[index]
        index = index + 1
    return row_dict


def refresh_job(service_id, job_id):
    # In the event we make a call to fetch a phone number or csv row data
    # and it is not there because the data has been purged from redis,
    # we can refresh it making this call
    data = s3_csv_client.s3download(service_id, job_id)
    add_row_data_to_redis(data, job_id)
