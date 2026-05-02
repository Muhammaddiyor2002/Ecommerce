"""Payme.uz JSON-RPC provider (Merchant API).

Payme uses Basic auth with a static merchant key + JSON-RPC method names like
``CheckPerformTransaction``, ``CreateTransaction``, ``PerformTransaction``,
``CancelTransaction``. We accept the JSON body and route to the correct
internal status.
"""

from __future__ import annotations

import base64
import json
import logging
from decimal import Decimal

from django.conf import settings

from .base import BasePaymentProvider, ChargeIntent, ChargeResult, WebhookResult

logger = logging.getLogger(__name__)


class PaymeProvider(BasePaymentProvider):
    code = "payme"

    def __init__(self) -> None:
        self.merchant_id = getattr(settings, "PAYME_MERCHANT_ID", "") or ""
        self.secret_key = getattr(settings, "PAYME_SECRET_KEY", "") or ""

    def create_charge(self, intent: ChargeIntent) -> ChargeResult:
        if not self.merchant_id:
            return ChargeResult(success=False, error="payme not configured")
        # Build the standard Payme deeplink (base64 of params).
        params = (
            f"m={self.merchant_id};"
            f"ac.order_id={intent.order_id};"
            f"a={int((intent.amount * Decimal('100')).to_integral_value())};"
            f"l=en"
        )
        encoded = base64.b64encode(params.encode()).decode()
        return ChargeResult(
            success=True,
            redirect_url=f"https://checkout.paycom.uz/{encoded}",
            provider_reference=intent.order_id,
        )

    def _verify_basic_auth(self, headers: dict) -> bool:
        auth = headers.get("Authorization") or headers.get("authorization", "")
        if not auth.lower().startswith("basic "):
            return False
        try:
            decoded = base64.b64decode(auth.split(" ", 1)[1]).decode()
            user, _, password = decoded.partition(":")
        except Exception:
            return False
        return user == "Paycom" and password == self.secret_key

    def parse_webhook(
        self, *, headers: dict, body: bytes, raw_signature: str = ""
    ) -> WebhookResult:
        if not self._verify_basic_auth(headers):
            return WebhookResult(accepted=False, error="basic auth failed")
        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            return WebhookResult(accepted=False, error=str(exc))
        method = payload.get("method", "")
        params = payload.get("params", {})
        order_id = (params.get("account") or {}).get("order_id", "")

        new_status = ""
        if method == "PerformTransaction":
            new_status = "captured"
        elif method == "CreateTransaction":
            new_status = "authorized"
        elif method == "CancelTransaction":
            new_status = "cancelled"
        return WebhookResult(
            accepted=True,
            event_type=method,
            order_id=order_id,
            payment_reference=params.get("id", ""),
            new_status=new_status,
            raw=payload,
        )
