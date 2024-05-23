# What's currently available in the API?

* Models
  * `AnnualBilling` has `free_sms_fragment_limit`
  * `FactBilling` has `billable_units`, `rate`, `rate_multiplier`
  * `FactNotificationStatus` has `notification_count`
  * `Service` has `message_limit`, `total_message_limit`, `volume_sms`
  * `FactProcessingTime` has `messages_total`, `messages_within_10_secs`
* Routes
  * The billing `monthly-usage` and `yearly_usage_summary` routes have some pieces of data, from the above models: `chargable_units`, `notifications_sent`, `rate`, `cost`, `free_allowance_used`, and `charged_units`
  * The performance dashboard has `total_notifications`, `sms_notifications`, `notifications_by_type`, and `live_service_count`
  * The platform statistics `volumes-by-service` has `sms_notifications`, `free_allowance`, `sms_chargeable_units`

# What might we be able to consolidate or clean up?

Without knowing exactly what we are actually using in the system, I am not certain. From my reading of everything, it looks relatively good as it stands - Other than the obvious eventual removal of email statistics from the system.

# What might we need to do/create?

I believe a new endpoint for the allowance countdown makes the most sense. Something that can provide the data needed for the component. It looks like we might have the information we need contained in the models I have identified above, but it might need some aggregation of data to get the numbers we need.

# What work might already be in flight and incomplete/not reviewed yet?

There doesn't appear to be any other work in flight for this project.

# What is an estimated level of effort for each feature based on previous questions?

The main thing would be making the new endpoint. I believe there already is the data needed for it, just it might need some determination as to how to approach the math to get the numbers we need exactly from the models we already have. But, this seems fairly straight-forward, and I believe would be probably a fib. scale of 3, based on what I've seen.
