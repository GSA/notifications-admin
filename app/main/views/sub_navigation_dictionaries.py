def features_nav():
    return [
        {
            "name": "Features",
            "link": "main.features",
            "sub_navigation_items": [
                # {
                #     "name": "Text messages",
                #     "link": "main.features_sms",
                # },
            ],
        },
        {
            "name": "Roadmap",
            "link": "main.roadmap",
        },
        {
            "name": "Security",
            "link": "main.security",
        },
    ]


def using_notify_nav():
    return [
        {
            "name": "Get started",
            "link": "main.get_started",
        },
        {
            "name": "Guides",
            "link": "main.best_practices",
        },
        {
            "name": "Trial mode",
            "link": "main.trial_mode_new",
        },
        {
            "name": "Tracking usage",
            "link": "main.pricing",
        },
        {
            "name": "Delivery status",
            "link": "main.message_status",
        },
        {
            "name": "Guidance",
            "link": "main.guidance_index",
            # "sub_navigation_items": [
            #     {
            #         "name": "Formatting",
            #         "link": "main.edit_and_format_messages",
            #     },
            #     {
            #        "name": "Send files by email",
            #        "link": "main.send_files_by_email",
            #     },
            # ]
            # {
            #   "name": "API documentation",
            #   "link": "main.documentation",
            # },
        },
    ]


def best_practices_nav():
    return [
        {
            "name": "Best Practices",
            "link": "main.best_practices",
        },
        {
            "name": "Clear goals",
            "link": "main.clear_goals",
        },
        {
            "name": "Rules and regulations",
            "link": "main.rules_and_regulations",
        },
        {
            "name": "Establish trust",
            "link": "main.establish_trust",
            "sub_navigation_items": [
                {
                    "name": "Get the word out",
                    "link": "main.establish_trust#get-the-word-out",
                },
                {
                    "name": "As people receive texts",
                    "link": "main.establish_trust#as-people-receive-texts",
                },
            ],
        },
        {
            "name": "Write for action",
            "link": "main.write_for_action",
        },
        {
            "name": "Multiple languages",
            "link": "main.multiple_languages",
        },
        {
            "name": "Benchmark performance",
            "link": "main.benchmark_performance",
        },
    ]


def about_notify_nav():
    return [
        {
            "name": "About notify",
            "link": "main.about_notify",
        },
        {
            "name": "Security",
            "link": "main.about_security",
        },
    ]
