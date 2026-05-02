"""Payment orchestration: create charge, handle webhook results."""

from __future__ import annotations

import dataclasses
import logging

from django.db import transaction

from apps.orders.models import Order, OrderEvent
from apps.orders.services import transition_status

from .models import Payment
from .providers import ChargeIntent, get_provider

logger = logging.getLogger(__name__)


def _jsonable(value):
    """Recursively coerce SDK objects to JSON-safe primitives."""
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, str | int | float | bool | type(None)):
        return value
    return str(value)


@transaction.atomic
def create_payment(
    *, order: Order, provider_code: str, success_url: str = "", cancel_url: str = ""
) -> Payment:
    provider = get_provider(provider_code)
    intent = ChargeIntent(
        order_id=str(order.id),
        order_number=order.number,
        amount=order.grand_total,
        currency=order.currency,
        customer_email=order.email_snapshot,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"order_id": str(order.id)},
    )
    payment = Payment.objects.create(
        order=order,
        provider=provider_code,
        amount=order.grand_total,
        currency=order.currency,
        raw_request=_jsonable(dataclasses.asdict(intent)),
    )
    result = provider.create_charge(intent)
    if not result.success:
        payment.status = Payment.Status.FAILED
        payment.error = {"message": result.error}
        payment.save(update_fields=["status", "error", "updated_at"])
        return payment
    payment.status = Payment.Status.PENDING
    payment.provider_reference = result.provider_reference
    payment.provider_intent_id = result.intent_id
    payment.redirect_url = result.redirect_url
    payment.raw_response = _jsonable(result.raw)
    payment.save(
        update_fields=[
            "status",
            "provider_reference",
            "provider_intent_id",
            "redirect_url",
            "raw_response",
            "updated_at",
        ]
    )
    order.payment_provider = provider_code
    order.payment_reference = result.provider_reference
    order.save(update_fields=["payment_provider", "payment_reference", "updated_at"])
    return payment


@transaction.atomic
def handle_webhook(*, provider_code: str, headers: dict, body: bytes) -> dict:
    provider = get_provider(provider_code)
    parsed = provider.parse_webhook(headers=headers, body=body)
    if not parsed.accepted:
        logger.warning("rejected %s webhook: %s", provider_code, parsed.error)
        return {"accepted": False, "error": parsed.error}

    order = None
    if parsed.order_id:
        try:
            order = Order.objects.select_for_update().get(pk=parsed.order_id)
        except Order.DoesNotExist:
            order = None
    if order is None and parsed.payment_reference:
        order = (
            Order.objects.select_for_update()
            .filter(payment_reference=parsed.payment_reference)
            .first()
        )
    if order is None:
        logger.warning("webhook for unknown order: %s", parsed.raw)
        return {"accepted": True, "matched": False}

    OrderEvent.objects.create(
        order=order,
        code=f"webhook:{parsed.event_type}",
        message="payment provider webhook",
        payload=parsed.raw,
    )

    if parsed.new_status == "captured":
        try:
            transition_status(order=order, new_status=Order.Status.PAID, message="paid via webhook")
        except Exception as exc:  # pragma: no cover
            logger.exception("transition to PAID failed: %s", exc)
    elif parsed.new_status in {"failed", "cancelled"} and order.status == Order.Status.PENDING:
        transition_status(
            order=order,
            new_status=Order.Status.CANCELLED,
            message=f"cancelled via webhook ({parsed.new_status})",
        )
    elif parsed.new_status == "refunded":
        transition_status(
            order=order, new_status=Order.Status.REFUNDED, message="refunded via webhook"
        )

    Payment.objects.filter(order=order, provider=provider_code).update(
        status=parsed.new_status or Payment.Status.PENDING.value,
        raw_response=parsed.raw,
    )
    return {"accepted": True, "matched": True, "order": order.number}
