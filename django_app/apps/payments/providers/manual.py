"""Manual (cash on delivery / bank transfer) — admin-confirmed payments."""

from __future__ import annotations

from .base import BasePaymentProvider, ChargeIntent, ChargeResult, WebhookResult


class ManualProvider(BasePaymentProvider):
    code = "manual"

    def create_charge(self, intent: ChargeIntent) -> ChargeResult:
        return ChargeResult(success=True, provider_reference=f"manual:{intent.order_id}")

    def parse_webhook(
        self, *, headers: dict, body: bytes, raw_signature: str = ""
    ) -> WebhookResult:
        # Manual provider has no webhooks — admin confirms via the dashboard.
        return WebhookResult(accepted=False, error="no webhook for manual provider")
