"""Pricing engine service scaffolding (no business logic in Part 1)."""


def get_pricing_campaign_policy():
    return {
        "status": "not_implemented",
        "pricing_campaign_mode": {
            "is_active": False,
            "start_at": None,
            "end_at": None,
            "scope": "both",
        },
    }


def update_pricing_campaign_policy(payload: dict):
    return {
        "status": "not_implemented",
        "message": "Pricing campaign policy scaffold",
        "payload": payload,
    }


def get_pricing_quote(payload: dict):
    return {
        "status": "not_implemented",
        "message": "Pricing quote scaffold",
        "payload": payload,
    }


def list_pricing_packages():
    return {
        "status": "not_implemented",
        "packages": [],
    }
