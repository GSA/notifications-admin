import csv
import io

from app.utils.csv import (
    convert_report_date_to_preferred_timezone,
    get_user_preferred_timezone,
)


def convert_s3_csv_timestamps(csv_content, user_timezone=None):
    """
    Convert UTC timestamps in CSV to user's preferred timezone.

    Args:
        csv_content: The CSV content as string or bytes
        user_timezone: Optional pre-captured timezone (to avoid context issues in streaming)
    """
    if isinstance(csv_content, bytes):
        csv_content = csv_content.decode("utf-8")

    if user_timezone is None:
        user_timezone = get_user_preferred_timezone()

    reader = csv.reader(io.StringIO(csv_content))

    time_column_index = None
    try:
        header = next(reader)
        for i, col in enumerate(header):
            if col.strip().lower() == "time":
                time_column_index = i
                break

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(header)
        yield output.getvalue()
        output.truncate(0)
        output.seek(0)
    except StopIteration:
        return

    if time_column_index is None:
        for row in reader:
            writer.writerow(row)
            yield output.getvalue()
            output.truncate(0)
            output.seek(0)
        return

    for row in reader:
        if len(row) > time_column_index and row[time_column_index]:
            try:
                row[time_column_index] = convert_report_date_to_preferred_timezone(
                    row[time_column_index], target_timezone=user_timezone
                )
            except Exception:  # nosec B110
                pass

        writer.writerow(row)
        yield output.getvalue()
        output.truncate(0)
        output.seek(0)
