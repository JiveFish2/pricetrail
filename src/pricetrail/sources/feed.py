"""A store read from its product feed (Shopify-flavoured Atom).

One request returns every listed product with the price of each variant. An
offer that is not in the feed any more is reported as not read, so the run
shows up as partial instead of inventing an "unavailable" price point.

The external id is the numeric product id that ends the entry's `<id>` URL.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from decimal import Decimal

from pricetrail.http import Client
from pricetrail.sources.base import Observation, Offer

NS = {"atom": "http://www.w3.org/2005/Atom", "s": "http://jadedpixel.com/-/spec/shopify"}

log = logging.getLogger(__name__)


class AtomFeedSource:
    kind = "feed"

    def __init__(
        self, *, id: str, name: str, homepage: str, currency: str, feed_url: str, client: Client
    ) -> None:
        self.id = id
        self.name = name
        self.homepage = homepage
        self.currency = currency
        self.feed_url = feed_url
        self.client = client

    def fetch(self, offers: list[Offer]) -> list[Observation]:
        response = self.client.get(self.feed_url)
        listed = parse_feed(response.text, currency=self.currency)
        observations: list[Observation] = []
        for offer in offers:
            price = listed.get(offer.external_id)
            if price is None:
                log.warning("%s: product %s not in the feed, skipping", self.id, offer.external_id)
                continue
            observations.append(Observation(offer.id, price, None, True))
        return observations


def parse_feed(xml: str, *, currency: str) -> dict[str, Decimal]:
    """Map product id -> lowest variant price in `currency`.

    Entries whose variants are all in another currency are left out.
    """
    root = ET.fromstring(xml)
    prices: dict[str, Decimal] = {}
    for entry in root.findall("atom:entry", NS):
        id_element = entry.find("atom:id", NS)
        if id_element is None or not id_element.text:
            continue
        product_id = id_element.text.rstrip("/").rsplit("/", 1)[-1]
        variant_prices = [
            Decimal(price.text)
            for price in entry.findall("s:variant/s:price", NS)
            if price.text and price.get("currency", currency) == currency
        ]
        if variant_prices:
            prices[product_id] = min(variant_prices)
    return prices
