"""Click.uz (Uzbekistan) — Merchant API integration.

Click sends server-to-server callbacks (``Prepare`` & ``Complete`` actions). We
verify the MD5 sign string defined in their docs and translate to the internal
payment status.
"""

from __future__ import annotations

import hashlib
import logging

from django.conf import settings

from .base import BasePaymentProvider, ChargeIntent, ChargeResult, WebhookResult

logger = logging.getLogger(__name__)


class ClickProvider(BasePaymentProvider):
    code = "click"

    def __init__(self) -> None:
        self.service_id = getattr(settings, "CLICK_SERVICE_ID", "") or ""
        self.merchant_id = getattr(settings, "CLICK_MERCHANT_ID", "") or ""
        self.secret_key = getattr(settings, "CLICK_SECRET_KEY", "") or ""

    def create_charge(self, intent: ChargeIntent) -> ChargeResult:
        if not self.service_id:
            return ChargeResult(success=False, error="click not configured")
        # Click's redirect url pattern: https://my.click.uz/services/pay
        redirect = (
            f"https://my.click.uz/services/pay"
            f"?service_id={self.service_id}"
            f"&merchant_id={self.merchant_id}"
            f"&amount={intent.amount}"
            f"&transaction_param={intent.order_number}"
            f"&return_url={intent.success_url}"
        )
        return ChargeResult(
            success=True, redirect_url=redirect, provider_reference=intent.order_number
        )

    def _expected_sign(self, p: dict, action: int) -> str:
        # md5(click_trans_id + service_id + secret_key + merchant_trans_id +
        #     [merchant_prepare_id] + amount + action + sign_time)
        parts = [
            str(p.get("click_trans_id", "")),
            str(p.get("service_id", "")),
            self.secret_key,
            str(p.get("merchant_trans_id", "")),
        ]
        if action == 1:
            parts.append(str(p.get("merchant_prepare_id", "")))
        parts.append(str(p.get("amount", "")))
        parts.append(str(action))
        parts.append(str(p.get("sign_time", "")))
        return hashlib.md5("".join(parts).encode()).hexdigest()

    def parse_webhook(
        self, *, headers: dict, body: bytes, raw_signature: str = ""
    ) -> WebhookResult:
        # Body for Click is application/x-www-form-urlencoded.
        from urllib.parse import parse_qs

        params = {k: v[0] for k, v in parse_qs(body.decode("utf-8", "ignore")).items()}
        try:
            action = int(params.get("action", "0"))
        except ValueError:
            return WebhookResult(accepted=False, error="bad action")

        expected = self._expected_sign(params, action)
        if expected.lower() != (params.get("sign_string", "") or "").lower():
            return WebhookResult(accepted=False, error="signature mismatch", raw=params)

        order_number = params.get("merchant_trans_id", "")
        new_status = ""
        if action == 0:
            new_status = "authorized"
        elif action == 1:
            new_status = "captured"
        return WebhookResult(
            accepted=True,
            event_type=f"click.action.{action}",
            order_id="",
            payment_reference=order_number,
            new_status=new_status,
            raw=params,
        )
