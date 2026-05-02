"""Payment provider plug-ins.

Each provider implements :class:`BasePaymentProvider` and is registered in
``REGISTRY``. Code outside of this package never imports a specific provider —
it goes through :func:`get_provider`.
"""

from __future__ import annotations

from .base import BasePaymentProvider, ChargeIntent, ChargeResult, WebhookResult
from .click import ClickProvider
from .manual import ManualProvider
from .payme import PaymeProvider
from .paypal import PayPalProvider
from .stripe_provider import StripeProvider

REGISTRY: dict[str, type[BasePaymentProvider]] = {
    "stripe": StripeProvider,
    "paypal": PayPalProvider,
    "click": ClickProvider,
    "payme": PaymeProvider,
    "manual": ManualProvider,
}


def get_provider(name: str) -> BasePaymentProvider:
    cls = REGISTRY.get(name)
    if not cls:
        raise ValueError(f"unknown payment provider: {name}")
    return cls()


__all__ = (
    "REGISTRY",
    "BasePaymentProvider",
    "ChargeIntent",
    "ChargeResult",
    "WebhookResult",
    "get_provider",
)
