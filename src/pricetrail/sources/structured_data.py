"""Reads schema.org Product offers out of an HTML page.

Stores publish the same data in two shapes: JSON-LD blocks
(`<script type="application/ld+json">`) or microdata attributes
(`<meta itemprop="price" content="...">`). This module understands both and
returns plain `PageOffer` records, using only the standard library.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from typing import Any

IN_STOCK = {"InStock", "PreOrder", "PreSale", "LimitedAvailability", "OnlineOnly", "InStoreOnly"}


@dataclass
class PageOffer:
    price: Decimal | None = None
    currency: str | None = None
    available: bool | None = None

    @property
    def complete(self) -> bool:
        return self.price is not None


def parse_offers(html: str) -> list[PageOffer]:
    """Every offer found on the page, JSON-LD first, then microdata."""
    parser = _Parser()
    parser.feed(html)
    offers: list[PageOffer] = []
    for block in parser.json_ld_blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        offers.extend(_offers_from_json_ld(data))
    offers.extend(offer for offer in parser.microdata_offers if offer.complete)
    return offers


def best_offer(html: str) -> PageOffer | None:
    """The cheapest in-stock offer, or the cheapest one when nothing is in stock."""
    offers = [offer for offer in parse_offers(html) if offer.complete]
    if not offers:
        return None
    in_stock = [offer for offer in offers if offer.available]
    return min(in_stock or offers, key=lambda offer: offer.price)


# --- JSON-LD -----------------------------------------------------------------


def _offers_from_json_ld(data: Any) -> list[PageOffer]:
    found: list[PageOffer] = []
    for node in _walk(data):
        if not isinstance(node, dict):
            continue
        types = node.get("@type")
        types = types if isinstance(types, list) else [types]
        if "Product" not in types:
            continue
        offers = node.get("offers")
        offers = offers if isinstance(offers, list) else [offers]
        for offer in offers:
            if isinstance(offer, dict):
                found.append(_offer_from_dict(offer))
    return [offer for offer in found if offer.complete]


def _offer_from_dict(offer: dict[str, Any]) -> PageOffer:
    price = offer.get("price")
    if price is None:
        price = offer.get("lowPrice")  # AggregateOffer
    if price is None and isinstance(offer.get("priceSpecification"), dict):
        price = offer["priceSpecification"].get("price")
    return PageOffer(
        price=_decimal(price),
        currency=offer.get("priceCurrency"),
        available=_availability(offer.get("availability")),
    )


def _walk(node: Any):
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


# --- Microdata ----------------------------------------------------------------


class _Parser(HTMLParser):
    """Collects JSON-LD blocks and groups microdata price fields into offers.

    A new offer starts whenever a field that the current offer already has
    shows up again, which is how variant lists appear in the markup.
    """

    FIELDS = {"price", "priceCurrency", "availability"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.json_ld_blocks: list[str] = []
        self.microdata_offers: list[PageOffer] = []
        self._in_json_ld = False
        self._pending_field: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self._in_json_ld = True
            self.json_ld_blocks.append("")
            return
        field = attributes.get("itemprop")
        if field not in self.FIELDS:
            return
        content = attributes.get("content")
        if content is None and tag in ("link", "a"):
            content = attributes.get("href")  # URL-valued properties, e.g. availability
        if content is None:
            self._pending_field = field  # value is the element's text
        else:
            self._set(field, content)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_json_ld = False
        self._pending_field = None

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self.json_ld_blocks[-1] += data
        elif self._pending_field and data.strip():
            self._set(self._pending_field, data.strip())
            self._pending_field = None

    def _set(self, field: str, raw: str) -> None:
        current = self.microdata_offers[-1] if self.microdata_offers else None
        if current is None or _has(current, field):
            current = PageOffer()
            self.microdata_offers.append(current)
        if field == "price":
            current.price = _decimal(raw)
        elif field == "priceCurrency":
            current.currency = raw
        else:
            current.available = _availability(raw)


def _has(offer: PageOffer, field: str) -> bool:
    return {
        "price": offer.price is not None,
        "priceCurrency": offer.currency is not None,
        "availability": offer.available is not None,
    }[field]


# --- Shared ------------------------------------------------------------------


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    text = "".join(ch for ch in text if ch.isdigit() or ch == ".")
    try:
        return Decimal(text) if text else None
    except InvalidOperation:
        return None


def _availability(value: Any) -> bool | None:
    if not value:
        return None
    return str(value).rsplit("/", 1)[-1] in IN_STOCK
