"""A store read from its public product pages.

Each offer's URL is fetched and the price comes from the page's schema.org
markup (JSON-LD or microdata), so the same class serves any store that
publishes structured data. Pages take one request each, so this source is the
slowest and is kept to a handful of products.
"""

from __future__ import annotations

import logging

import httpx

from pricetrail.http import Client
from pricetrail.sources.base import Observation, Offer
from pricetrail.sources.structured_data import best_offer

log = logging.getLogger(__name__)


class ProductPageSource:
    kind = "html"

    def __init__(self, *, id: str, name: str, homepage: str, currency: str, client: Client) -> None:
        self.id = id
        self.name = name
        self.homepage = homepage
        self.currency = currency
        self.client = client

    def fetch(self, offers: list[Offer]) -> list[Observation]:
        observations: list[Observation] = []
        for offer in offers:
            try:
                response = self.client.get(offer.url)
            except httpx.HTTPStatusError as error:
                if error.response.status_code in (404, 410):
                    log.warning(
                        "%s: %s is gone (HTTP %d), skipping",
                        self.id,
                        offer.url,
                        error.response.status_code,
                    )
                    continue
                raise
            found = best_offer(response.text)
            if found is None:
                log.warning("%s: no structured price on %s, skipping", self.id, offer.url)
                continue
            if found.currency and found.currency != self.currency:
                log.warning(
                    "%s: %s priced in %s, expected %s, skipping",
                    self.id,
                    offer.url,
                    found.currency,
                    self.currency,
                )
                continue
            available = found.available is not False
            observations.append(
                Observation(offer.id, found.price if available else None, None, available)
            )
        return observations
