"""Stripe provider — checkout session + webhook validation."""

from __future__ import annotations

import hmac
import logging
from decimal import Decimal
from typing import Any

from django.conf import settings

from .base import BasePaymentProvider, ChargeIntent, ChargeResult, WebhookResult

logger = logging.getLogger(__name__)


class StripeProvider(BasePaymentProvider):
    code = "stripe"

    def __init__(self) -> None:
        self.api_key = getattr(settings, "STRIPE_API_KEY", "") or ""
        self.webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or ""

    # ---------- create ----------
    def create_charge(self, intent: ChargeIntent) -> ChargeResult:
        if not self.api_key:
            return ChargeResult(success=False, error="stripe not configured")
        try:
            import stripe
        except ImportError:  # pragma: no cover
            return ChargeResult(success=False, error="stripe sdk not installed")

        stripe.api_key = self.api_key
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[
                    {
                        "quantity": 1,
                        "price_data": {
                            "currency": intent.currency.lower(),
                            "unit_amount": int(
                                (intent.amount * Decimal("100")).to_integral_value()
                            ),
                            "product_data": {"name": f"Order {intent.order_number}"},
                        },
                    }
                ],
                customer_email=intent.customer_email,
                client_reference_id=intent.order_id,
                success_url=intent.success_url or "https://example.com/success",
                cancel_url=intent.cancel_url or "https://example.com/cancel",
                metadata={"order_id": intent.order_id, "order_number": intent.order_number},
            )
            return ChargeResult(
                success=True,
                provider_reference=session.id,
                intent_id=session.payment_intent or "",
                redirect_url=session.url or "",
                raw=session.to_dict(),
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("stripe create_charge failed")
            return ChargeResult(success=False, error=str(exc))

    # ---------- webhook ----------
    def parse_webhook(
        self, *, headers: dict, body: bytes, raw_signature: str = ""
    ) -> WebhookResult:
        if not self.webhook_secret:
            return WebhookResult(accepted=False, error="stripe webhook secret not configured")
        try:
            import stripe
        except ImportError:  # pragma: no cover
            return WebhookResult(accepted=False, error="stripe sdk not installed")

        sig = (
            raw_signature or headers.get("Stripe-Signature") or headers.get("stripe-signature", "")
        )
        try:
            event = stripe.Webhook.construct_event(body, sig, self.webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError) as exc:  # pragma: no cover
            return WebhookResult(accepted=False, error=f"signature: {exc}")

        return self._map_event(event)

    def _map_event(self, event: Any) -> WebhookResult:
        type_ = event.get("type") if isinstance(event, dict) else event["type"]
        data = (event.get("data") or {}).get("object", {}) if isinstance(event, dict) else {}
        order_id = (data.get("metadata") or {}).get("order_id", "")
        ref = data.get("id", "")
        if type_ in {"checkout.session.completed", "payment_intent.succeeded"}:
            new_status = "captured"
        elif type_ in {"payment_intent.payment_failed", "checkout.session.expired"}:
            new_status = "failed"
        elif type_ in {"charge.refunded", "refund.created"}:
            new_status = "refunded"
        else:
            return WebhookResult(accepted=True, event_type=type_, raw=data)
        return WebhookResult(
            accepted=True,
            event_type=type_,
            order_id=order_id,
            payment_reference=ref,
            new_status=new_status,
            raw=data,
        )

    # ---------- helpers ----------
    def constant_time_compare(self, a: str, b: str) -> bool:
        return hmac.compare_digest(a.encode(), b.encode())
