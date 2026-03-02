"""P0-04: Legacy billing webhook route module removed.

Not: Tarihi test scriptleri bu modülden fonksiyon import ediyorsa
çalışma anında açık hata alması için no-op yerine explicit RuntimeError döner.
"""


def _removed(*_: object, **__: object) -> None:
    raise RuntimeError("Legacy billing webhook flow removed in P0-04")


handle_checkout_completed = _removed
handle_payment_succeeded = _removed
handle_subscription_deleted = _removed

__all__ = [
    "handle_checkout_completed",
    "handle_payment_succeeded",
    "handle_subscription_deleted",
]
