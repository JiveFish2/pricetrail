"""Sends price-drop emails for confirmed alerts whose target has been reached.

Runs right after `collect`. Each alert fires once: `notified_at` is set in the
same transaction as the send, and the email carries the unsubscribe link.
Without RESEND_API_KEY the message is logged instead of sent.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from decimal import Decimal

import httpx
import psycopg

RESEND_URL = "https://api.resend.com/emails"

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DueAlert:
    id: int
    email: str
    target_price: Decimal
    price: Decimal
    currency: str
    product: str
    product_slug: str
    source: str
    offer_url: str
    unsubscribe_token: str


def due_alerts(conn: psycopg.Connection) -> list[DueAlert]:
    with conn.cursor() as cur:
        cur.execute(
            """
            with latest as (
                select distinct on (offer_id) offer_id, price, available
                from price_points order by offer_id, observed_at desc
            )
            select a.id, a.email, a.target_price, l.price, s.currency, p.name, p.slug, s.name,
                   o.url, a.unsubscribe_token
            from alerts a
            join offers o on o.id = a.offer_id
            join sources s on s.id = o.source_id
            join products p on p.id = o.product_id
            join latest l on l.offer_id = o.id
            where a.confirmed_at is not null
              and a.notified_at is null
              and l.available
              and l.price <= a.target_price
            order by a.id
            """
        )
        return [DueAlert(*row) for row in cur.fetchall()]


def notify(conn: psycopg.Connection, site_url: str) -> int:
    """Email every due alert and mark it notified. Returns how many were sent."""
    sent = 0
    for alert in due_alerts(conn):
        try:
            send_email(
                to=alert.email,
                subject=f"{alert.product} is now {money(alert.price, alert.currency)}",
                text=render(alert, site_url),
            )
        except Exception:  # noqa: BLE001 - one bad address must not block the rest
            log.exception("alert %d: send failed", alert.id)
            continue
        with conn.cursor() as cur:
            cur.execute("update alerts set notified_at = now() where id = %s", (alert.id,))
        conn.commit()
        sent += 1
    return sent


def render(alert: DueAlert, site_url: str) -> str:
    return "\n".join(
        [
            f"{alert.product} at {alert.source} is now {money(alert.price, alert.currency)},"
            f" at or below your target of {money(alert.target_price, alert.currency)}.",
            "",
            f"Open the store: {alert.offer_url}",
            f"Price history: {site_url}/p/{alert.product_slug}",
            "",
            "This alert has done its job and will not email you again."
            " To set a new target, visit the product page.",
            "Stop receiving alerts for this product:"
            f" {site_url}/alerts/unsubscribe/{alert.unsubscribe_token}",
        ]
    )


def money(value: Decimal, currency: str) -> str:
    amount = f"{value:,.2f}"
    if currency == "BRL":
        amount = amount.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {amount}"
    if currency == "USD":
        return f"${amount}"
    return f"{amount} {currency}"


def send_email(*, to: str, subject: str, text: str) -> None:
    key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("ALERT_FROM", "PriceTrail <alerts@example.com>")
    if not key:
        log.info("[email not sent: RESEND_API_KEY unset] to=%s subject=%s\n%s", to, subject, text)
        return
    response = httpx.post(
        RESEND_URL,
        headers={"Authorization": f"Bearer {key}"},
        json={"from": sender, "to": [to], "subject": subject, "text": text},
        timeout=20,
    )
    response.raise_for_status()
