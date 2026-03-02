from typing import Optional


STRIPE_EVENT_TO_PAYMENT_STATUS = {
    "payment_intent.created": "created",
    "payment_intent.processing": "processing",
    "payment_intent.requires_action": "processing",
    "payment_intent.requires_payment_method": "processing",
    "payment_intent.succeeded": "succeeded",
    "payment_intent.payment_failed": "failed",
    "payment_intent.canceled": "failed",
    "invoice.paid": "succeeded",
    "invoice.payment_failed": "failed",
}


PAYMENT_STATUS_TO_LISTING_STATUS = {
    "created": "payment_processing",
    "processing": "payment_processing",
    "succeeded": "active",
    "failed": "pending_payment",
}


def map_stripe_event_to_payment_status(event_type: str) -> Optional[str]:
    if not event_type:
        return None
    return STRIPE_EVENT_TO_PAYMENT_STATUS.get(str(event_type).strip().lower())


def map_payment_status_to_listing_status(payment_status: str) -> Optional[str]:
    if not payment_status:
        return None
    return PAYMENT_STATUS_TO_LISTING_STATUS.get(str(payment_status).strip().lower())


def map_stripe_intent_status_to_payment_status(intent_status: str) -> Optional[str]:
    if not intent_status:
        return None

    normalized = str(intent_status).strip().lower()
    if normalized == "succeeded":
        return "succeeded"
    if normalized in {"processing", "requires_action", "requires_confirmation", "requires_payment_method"}:
        return "processing"
    if normalized in {"canceled", "cancelled", "payment_failed", "failed"}:
        return "failed"
    return None
