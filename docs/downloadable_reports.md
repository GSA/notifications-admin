# Downloadable reports for sent messages and how they work

Downloadable reports related to sending messages are a little mysterious.  They can have a variable number of columns,
some of which contain PII, and it is not immediately clear what drives what gets displayed.  This is an explanation.

## Downloadable reports for one-off messages

When a user sends an ad-hoc message by typing in a phone number and sending, the downloadable report is only going to
show the bare minimum of columns.  There will be a column that shows the name of what template was used, but otherwise
there will be nothing beyond the bare basics of the phone number and the time sent, etc.

## Downloadable reports for jobs (uploaded csv files)

When a user uploads a csv file -- creating a job -- the downloadable report becomes more complex and interesting.

(Sample report)

|Row number|Phone number|name|date|time|address|English|Spanish|Template|Type|Job|Status|Time|
|----------|------------|----|----|----|-------|-------|-------|--------|----|---|------|----|
|1|17169829002|Tim|10/16|2:00 PM|5678 Tom St.|no|yes|Appointment reminder - 1 week|sms|US Notify Demo CSV - Copy of Sheet1 (11).csv|Sending|2023-07-18 15:25:54| 


In notifications_admin, in app.util.csv.py, there is a method called generate_notifications_csv().

It is using the service_id and job_id to look up the csv file in s3. It is then merging the standard
downloadable report (what we see in the one-off case mentioned above) with the custom csv data.

This means that the PII displayed is mostly not stored in the database, but rather is stored in S3.

The only PII stored in the database is the recipient's phone number, and that data is scrubbed.  If the
sms message is delivered successfully, the phone number is scrubbed immediately.  If the sms message
cannot be delivered, the PII will be scrubbed after seven days.