def using_notify_nav():
    nav_items = [
        {"name": "Get started", "link": "main.get_started"},
        {
            "name": "Best Practices",
            "link": "main.best_practices",
            "sub_navigation_items": [
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
        }
            ]
        },
        {"name": "Trial mode", "link": "main.trial_mode_new"},
        {"name": "Tracking usage", "link": "main.pricing"},
        {"name": "Delivery Status", "link": "main.message_status"},
        {"name": "Guidance", "link": "main.guidance_index"},
    ]

    return nav_items


def about_notify_nav():
    return [
        {
            "name": "About Notify",
            "link": "main.about_notify",
            "sub_navigation_items": [
                {
                    "name": "Why text messaging",
                    "link": "main.why_text_messaging",
                },
                {
                    "name": "Security",
                    "link": "main.about_security",
                },
            ],
        },
        {
            "name": "Join Notify",
            "link": "main.join_notify",
        },
        {
            "name": "Contact us",
            "link": "main.contact",
        },
    ]
