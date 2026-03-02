from typing import Optional


STRIPE_EVENT_TO_PAYMENT_STATUS = {
    "payment_intent.created": "created",
    "payment_intent.processing": "processing",
    "payment_intent.succeeded": "succeeded",
    "payment_intent.payment_failed": "failed",
    "payment_intent.canceled": "failed",
}


PAYMENT_STATUS_TO_LISTING_STATUS = {
    "processing": None,
    "succeeded": "pending_moderation",
    "failed": "draft",
}


def map_stripe_event_to_payment_status(event_type: str) -> Optional[str]:
    if not event_type:
        return None
    return STRIPE_EVENT_TO_PAYMENT_STATUS.get(str(event_type).strip().lower())


def map_payment_status_to_listing_status(payment_status: str) -> Optional[str]:
    if not payment_status:
        return None
    return PAYMENT_STATUS_TO_LISTING_STATUS.get(str(payment_status).strip().lower())
