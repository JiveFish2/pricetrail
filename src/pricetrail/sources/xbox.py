"""Xbox Store, read from its public product pages.

The pages carry schema.org data only for games already on sale, so prices come
from the store state embedded in the page (`window.__PRELOADED_STATE__`), which
also covers pre-orders. One class serves several markets: the locale in the URL
sets the currency, so `xbox-us` and `xbox-br` are two sources sharing this
module. The external id is the Store product id (e.g. C3D891Z6TNQM).
"""

from __future__ import annotations

import json
import logging
import re
from decimal import Decimal
from typing import Any

import httpx

from pricetrail.http import Client
from pricetrail.sources.base import Observation, Offer

STATE_START = re.compile(r"window\.__PRELOADED_STATE__\s*=\s*")

log = logging.getLogger(__name__)


class XboxSource:
    kind = "html"
    homepage = "https://www.xbox.com"

    def __init__(self, *, id: str, name: str, currency: str, client: Client) -> None:
        self.id = id
        self.name = name
        self.currency = currency
        self.client = client

    def fetch(self, offers: list[Offer]) -> list[Observation]:
        observations: list[Observation] = []
        for offer in offers:
            try:
                response = self.client.get(offer.url)
            except httpx.HTTPStatusError as error:
                if error.response.status_code in (404, 410):
                    log.warning("%s: %s is gone, skipping", self.id, offer.url)
                    continue
                raise
            parsed = parse_product_page(response.text, offer.external_id)
            if parsed is None:
                log.warning("%s: no price for %s on its page, skipping", self.id, offer.external_id)
                continue
            price, list_price, currency, image_url = parsed
            if currency != self.currency:
                log.warning(
                    "%s: %s priced in %s, expected %s, skipping",
                    self.id,
                    offer.external_id,
                    currency,
                    self.currency,
                )
                continue
            observations.append(Observation(offer.id, price, list_price, True, image_url))
        return observations


def parse_product_page(
    html: str, product_id: str
) -> tuple[Decimal, Decimal | None, str, str | None] | None:
    """(price, list_price, currency, image_url) of a product, or None when it
    cannot be bought.

    A product has one or more SKUs, each with a preferred availability that
    carries the price. Only availabilities that allow a purchase count; the
    cheapest one wins. `list_price` is the store's regular price, set only when
    the current price is lower. The image is the wide hero art, the shape the
    site's cards use.
    """
    state = _state(html)
    if state is None:
        return None
    products = state.get("core2", {}).get("products", {})
    skus = products.get("skuSummaries", {}).get(product_id) or {}
    availabilities = products.get("availabilitySummaries", {}).get(product_id) or {}

    best: tuple[Decimal, Decimal | None, str] | None = None
    for sku_id, sku in skus.items():
        availability = (availabilities.get(sku_id) or {}).get(sku.get("preferredAvailabilityId"))
        if not availability or "Purchase" not in availability.get("actions", []):
            continue
        price_info = availability.get("price") or {}
        if price_info.get("listPrice") is None or not price_info.get("currency"):
            continue
        price = Decimal(str(price_info["listPrice"]))
        msrp = Decimal(str(price_info.get("msrp", price_info["listPrice"])))
        if best is None or price < best[0]:
            best = (price, msrp if msrp > price else None, price_info["currency"])
    if best is None:
        return None
    images = (products.get("productSummaries", {}).get(product_id) or {}).get("images") or {}
    image_url = (images.get("superHeroArt") or {}).get("url")
    return (*best, image_url)


def _state(html: str) -> dict[str, Any] | None:
    match = STATE_START.search(html)
    if match is None:
        return None
    try:
        state, _ = json.JSONDecoder().raw_decode(html, match.end())
    except json.JSONDecodeError:
        return None
    return state if isinstance(state, dict) else None
