"""Provider abstract base — every gateway implements this contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(slots=True)
class ChargeIntent:
    order_id: str
    order_number: str
    amount: Decimal
    currency: str
    customer_email: str
    success_url: str = ""
    cancel_url: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class ChargeResult:
    success: bool
    provider_reference: str = ""
    redirect_url: str = ""
    intent_id: str = ""
    raw: dict = field(default_factory=dict)
    error: str = ""


@dataclass(slots=True)
class WebhookResult:
    """Outcome of a webhook validation/parse."""

    accepted: bool
    event_type: str = ""
    order_id: str = ""
    payment_reference: str = ""
    new_status: str = ""  # one of Payment.Status values
    raw: dict = field(default_factory=dict)
    error: str = ""


class BasePaymentProvider(ABC):
    """Concrete providers implement these methods."""

    code: str = ""

    @abstractmethod
    def create_charge(self, intent: ChargeIntent) -> ChargeResult: ...

    @abstractmethod
    def parse_webhook(
        self, *, headers: dict, body: bytes, raw_signature: str = ""
    ) -> WebhookResult: ...

    def refund(self, *, provider_reference: str, amount: Decimal) -> dict:  # pragma: no cover
        raise NotImplementedError
