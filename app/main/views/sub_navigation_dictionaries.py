def features_nav():
    return [
        {
            "name": "Features",
            "link": "main.features",
            "sub_navigation_items": [
                {
                    "name": "Emails",
                    "link": "main.features_email",
                },
                {
                    "name": "Text messages",
                    "link": "main.features_sms",
                },
            ]
        },
        {
            "name": "Roadmap",
            "link": "main.roadmap",
        },
        {
            "name": "Security",
            "link": "main.security",
        },
        {
            "name": "Terms of use",
            "link": "main.terms",
        },
    ]


def using_notify_nav():
    return [
        {
            "name": "Get started",
            "link": "main.get_started",
        },
        {
            "name": "Pricing",
            "link": "main.pricing",
        },
        {
            "name": "Trial mode",
            "link": "main.trial_mode_new",
        },
        {
            "name": "Delivery status",
            "link": "main.message_status",
        },
        {
            "name": "Guidance",
            "link": "main.guidance_index",
            "sub_navigation_items": [
                {
                    "name": "Formatting",
                    "link": "main.edit_and_format_messages",
                },
                # {
                #   "name": "Branding",
                #    "link": "main.branding_and_customisation",
                # },
                # {
                #    "name": "Send files by email",
                #    "link": "main.send_files_by_email",
                # },
            ]
        },
        # {
        #   "name": "API documentation",
        #   "link": "main.documentation",
        # },
    ]
