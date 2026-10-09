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
from html import escape

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
    image_url: str | None = None


def due_alerts(conn: psycopg.Connection) -> list[DueAlert]:
    with conn.cursor() as cur:
        cur.execute(
            """
            with latest as (
                select distinct on (offer_id) offer_id, price, available
                from price_points order by offer_id, observed_at desc
            )
            select a.id, a.email, a.target_price, l.price, s.currency, p.name, p.slug, s.name,
                   o.url, a.unsubscribe_token, p.image_url
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
                html=render_html(alert, site_url),
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


# The HTML version follows the site: warm paper, dark ink, a serif headline,
# mono for numbers, green for the drop. Tables and inline styles only, because
# that is what every mail client renders the same way.
SERIF = "Georgia, 'Times New Roman', serif"
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, Menlo, Consolas, monospace"


def render_html(alert: DueAlert, site_url: str) -> str:
    product = escape(alert.product)
    source = escape(alert.source)
    price = escape(money(alert.price, alert.currency))
    target = escape(money(alert.target_price, alert.currency))
    history = escape(f"{site_url}/p/{alert.product_slug}", quote=True)
    store = escape(alert.offer_url, quote=True)
    unsubscribe = escape(f"{site_url}/alerts/unsubscribe/{alert.unsubscribe_token}", quote=True)
    image = (
        f'<tr><td style="padding:0 0 20px"><img src="{escape(alert.image_url, quote=True)}"'
        f' alt="{product}" width="512" style="display:block;width:100%;max-width:512px;'
        'height:auto;border:1px solid #ddd6c4;border-radius:6px;background:#ffffff"></td></tr>'
        if alert.image_url
        else ""
    )
    body = f"""\
<tr><td style="padding:0 0 6px;font:600 11px/1.4 {MONO};letter-spacing:.12em;
text-transform:uppercase;color:#0f7a53">Price alert</td></tr>
<tr><td style="padding:0 0 20px;font:400 30px/1.15 {SERIF};color:#1b1d1a">{product}
reached your price</td></tr>
{image}
<tr><td style="padding:0 0 22px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
style="border-collapse:collapse;border-top:1px solid #ddd6c4;border-bottom:1px solid #ddd6c4">
<tr>
<td style="padding:14px 0;font:400 12px/1.4 {SANS};color:#5f655d">Now at {source}<br>
<span style="font:600 26px/1.3 {MONO};color:#0f7a53">{price}</span></td>
<td align="right" style="padding:14px 0;font:400 12px/1.4 {SANS};color:#5f655d">Your target<br>
<span style="font:500 18px/1.3 {MONO};color:#1b1d1a">{target}</span></td>
</tr></table></td></tr>
<tr><td style="padding:0 0 22px">
<a href="{store}" style="display:inline-block;padding:12px 22px;border-radius:999px;
background:#1b1d1a;color:#fffdf7;font:600 14px/1 {SANS};text-decoration:none">Open the store</a>
<a href="{history}" style="display:inline-block;padding:12px 6px 12px 16px;color:#1b1d1a;
font:500 14px/1 {SANS}">Price history &rarr;</a></td></tr>
<tr><td style="font:400 13px/1.6 {SANS};color:#5f655d">This alert has done its job and will
not email you again. To set a new target, visit the product page.</td></tr>"""
    footer = f'<a href="{unsubscribe}" style="color:#5f655d">Stop alerts for this product</a>'
    return layout(f"{product} is now {price}", body, footer, site_url)


def layout(preheader: str, body: str, footer: str, site_url: str) -> str:
    home = escape(site_url, quote=True)
    return f"""\
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"></head>
<body style="margin:0;padding:0;background:#f4f0e6">
<div style="display:none;max-height:0;overflow:hidden">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f0e6">
<tr><td align="center" style="padding:32px 16px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px">
<tr><td style="padding:0 4px 16px;font:700 17px/1 {SANS};letter-spacing:-.01em;color:#1b1d1a">
<a href="{home}" style="color:#1b1d1a;text-decoration:none">Price<span
style="color:#0f7a53">Trail</span></a></td></tr>
<tr><td style="background:#fffdf7;border:1px solid #ddd6c4;border-radius:10px;padding:28px 24px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{body}</table>
</td></tr>
<tr><td style="padding:18px 4px 0;font:400 12px/1.6 {SANS};color:#9a9f95">{footer}<br>
Public product data, collected once a day.
<a href="{home}/status" style="color:#9a9f95">How collection works</a></td></tr>
</table></td></tr></table></body></html>"""


def money(value: Decimal, currency: str) -> str:
    amount = f"{value:,.2f}"
    if currency == "BRL":
        amount = amount.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {amount}"
    if currency == "USD":
        return f"${amount}"
    return f"{amount} {currency}"


def send_email(*, to: str, subject: str, text: str, html: str | None = None) -> None:
    key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("ALERT_FROM", "PriceTrail <alerts@example.com>")
    if not key:
        log.info("[email not sent: RESEND_API_KEY unset] to=%s subject=%s\n%s", to, subject, text)
        return
    response = httpx.post(
        RESEND_URL,
        headers={"Authorization": f"Bearer {key}"},
        json={"from": sender, "to": [to], "subject": subject, "text": text}
        | ({"html": html} if html else {}),
        timeout=20,
    )
    response.raise_for_status()
