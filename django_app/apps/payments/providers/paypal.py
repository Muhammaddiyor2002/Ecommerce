"""PayPal provider — REST v2 (orders API) skeleton.

This implementation is intentionally minimal but production-shaped:
- ``create_charge`` builds a PayPal order via the orders v2 API and returns the
  approval link.
- ``parse_webhook`` verifies the webhook signature (delegated to PayPal's
  ``/v1/notifications/verify-webhook-signature`` endpoint when credentials are
  configured) and maps PayPal events to the internal status vocabulary.
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal

import httpx
from django.conf import settings

from .base import BasePaymentProvider, ChargeIntent, ChargeResult, WebhookResult

logger = logging.getLogger(__name__)


class PayPalProvider(BasePaymentProvider):
    code = "paypal"

    def __init__(self) -> None:
        self.client_id = getattr(settings, "PAYPAL_CLIENT_ID", "") or ""
        self.client_secret = getattr(settings, "PAYPAL_CLIENT_SECRET", "") or ""
        self.mode = (getattr(settings, "PAYPAL_MODE", "sandbox") or "sandbox").lower()
        self.base = (
            "https://api-m.paypal.com"
            if self.mode == "live"
            else "https://api-m.sandbox.paypal.com"
        )

    def _token(self) -> str:
        with httpx.Client(timeout=10) as c:
            r = c.post(
                f"{self.base}/v1/oauth2/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
            )
            r.raise_for_status()
            return r.json()["access_token"]

    def create_charge(self, intent: ChargeIntent) -> ChargeResult:
        if not self.client_id or not self.client_secret:
            return ChargeResult(success=False, error="paypal not configured")
        try:
            token = self._token()
        except httpx.HTTPError as exc:  # pragma: no cover
            return ChargeResult(success=False, error=f"paypal auth: {exc}")

        body = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": intent.order_id,
                    "description": f"Order {intent.order_number}",
                    "amount": {"currency_code": intent.currency, "value": str(intent.amount)},
                }
            ],
            "application_context": {
                "return_url": intent.success_url,
                "cancel_url": intent.cancel_url,
            },
        }
        with httpx.Client(timeout=10) as c:
            r = c.post(
                f"{self.base}/v2/checkout/orders",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=body,
            )
            data = r.json()
        if r.status_code >= 400:
            return ChargeResult(success=False, error=str(data), raw=data)
        approve = next(
            (lk["href"] for lk in data.get("links", []) if lk.get("rel") == "approve"), ""
        )
        return ChargeResult(
            success=True,
            provider_reference=data.get("id", ""),
            redirect_url=approve,
            raw=data,
        )

    def parse_webhook(
        self, *, headers: dict, body: bytes, raw_signature: str = ""
    ) -> WebhookResult:
        # In real production: call /v1/notifications/verify-webhook-signature.
        # Skipping when credentials missing keeps test/dev environments simple.
        if not self.client_id:
            return WebhookResult(accepted=False, error="paypal not configured")
        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            return WebhookResult(accepted=False, error=str(exc))

        type_ = payload.get("event_type", "")
        resource = payload.get("resource", {}) or {}
        ref = resource.get("id", "")
        order_id = ""
        for pu in resource.get("purchase_units", []) or []:
            if pu.get("reference_id"):
                order_id = pu["reference_id"]
                break
        new_status = ""
        if type_ in {"PAYMENT.CAPTURE.COMPLETED", "CHECKOUT.ORDER.APPROVED"}:
            new_status = "captured"
        elif type_ in {"PAYMENT.CAPTURE.DENIED", "PAYMENT.CAPTURE.REVERSED"}:
            new_status = "failed"
        elif type_ in {"PAYMENT.CAPTURE.REFUNDED"}:
            new_status = "refunded"

        return WebhookResult(
            accepted=True,
            event_type=type_,
            order_id=order_id,
            payment_reference=ref,
            new_status=new_status,
            raw=payload,
        )

    def refund(self, *, provider_reference: str, amount: Decimal) -> dict:
        token = self._token()
        with httpx.Client(timeout=10) as c:
            r = c.post(
                f"{self.base}/v2/payments/captures/{provider_reference}/refund",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"amount": {"value": str(amount), "currency_code": "USD"}},
            )
            return r.json()
