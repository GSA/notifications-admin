from flask import (
    current_app,
)

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
    nav_items = [
        {"name": "Get started", "link": "main.get_started"},
        {"name": "Guides", "link": "main.best_practices"},
        {"name": "Trial mode", "link": "main.trial_mode_new"},
        {"name": "Tracking usage", "link": "main.pricing"},
        {"name": "Delivery Status", "link": "main.message_status"},
        {"name": "Guidance", "link": "main.guidance_index"},

    ]
    if not current_app.config.get("FEATURE_BEST_PRACTICES_ENABLED"):
        nav_items = [item for item in nav_items if item["link"] != "main.best_practices"]

    return nav_items


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
            "name": "About Notify",
            "link": "main.about_notify",
            "sub_navigation_items": [
                {
                    "name": "Why text messaging",
                    "link": "main.why_text_messaging",
                    "sub_sub_navigation_items": [
                        {
                            "name": "Reach people using a common method",
                            "link": "main.why_text_messaging#reach-people-using-a-common-method",
                        },
                        {
                            "name": "Improve customer experience",
                            "link": "main.why_text_messaging#improve-customer-experience",
                        },
                        {
                            "name": "What texting is best for",
                            "link": "main.why_text_messaging#what-texting-is-best-for",
                        },
                    ],
                },
                {
                    "name": "Security",
                    "link": "main.about_security",
                },
            ],
        },
    ]
