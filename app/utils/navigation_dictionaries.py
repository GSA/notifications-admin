def using_organization_nav():
    return [
        {
            "name": "Usage",
            "link": ".organization_dashboard",
            "requires_permission": False,
        },
        {
            "name": "Team members",
            "link": ".manage_org_users",
            "requires_permission": False,
        },
        {
            "name": "Settings",
            "link": ".organization_settings",
            "requires_permission": False,
        },
        {
            "name": "Trial mode services",
            "link": ".organization_trial_mode_services",
            "requires_permission": False,
        },
        {
            "name": "Billing",
            "link": ".organization_billing",
            "requires_permission": False,
        },
    ]
