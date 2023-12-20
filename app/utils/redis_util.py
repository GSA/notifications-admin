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
    row_count = 0
    for row in rows:
        row_list = row.split(",")
        redis_client.set(f"job_{job_id}_row_{row_count}", row)
        redis_client.set(
            f"job_{job_id}_row_{row_count}_phone_number", row_list[phone_index]
        )
        row_count = row_count + 1
