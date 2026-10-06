"""Steam storefront (public JSON endpoint, no key required).

One class serves several regions: the storefront returns the price in the
currency of the `cc` country code, so `steam-br` and `steam-us` are two sources
sharing this module. The external id is the Steam app id.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from pricetrail.http import Client
from pricetrail.sources.base import Observation, Offer

API_URL = "https://store.steampowered.com/api/appdetails"
BATCH_SIZE = 20

log = logging.getLogger(__name__)


class SteamSource:
    kind = "api"
    homepage = "https://store.steampowered.com"

    def __init__(self, *, id: str, name: str, cc: str, currency: str, client: Client) -> None:
        self.id = id
        self.name = name
        self.cc = cc
        self.currency = currency
        self.client = client

    def fetch(self, offers: list[Offer]) -> list[Observation]:
        by_external = {offer.external_id: offer for offer in offers}
        observations: list[Observation] = []
        ids = list(by_external)
        for start in range(0, len(ids), BATCH_SIZE):
            batch = ids[start : start + BATCH_SIZE]
            response = self.client.get(
                API_URL,
                params={
                    "appids": ",".join(batch),
                    "cc": self.cc,
                    "l": "en",
                    "filters": "price_overview",
                },
            )
            for external_id, parsed in parse_app_details(response.json()).items():
                offer = by_external.get(external_id)
                if offer is None:
                    continue
                if parsed is None:
                    log.warning("%s: app %s not found, skipping", self.id, external_id)
                    continue
                price, list_price, available = parsed
                observations.append(Observation(offer.id, price, list_price, available))
        return observations


def parse_app_details(
    payload: dict[str, Any],
) -> dict[str, tuple[Decimal | None, Decimal | None, bool] | None]:
    """Map app id -> (price, list_price, available), or None when the app is unknown.

    Steam prices are integers in cents. A free or unreleased app answers with
    `success: true` and an empty `data`, which we record as unavailable.
    """
    result: dict[str, tuple[Decimal | None, Decimal | None, bool] | None] = {}
    for app_id, entry in payload.items():
        if not entry.get("success"):
            result[app_id] = None
            continue
        data = entry.get("data") or {}
        overview = data.get("price_overview") if isinstance(data, dict) else None
        if not overview:
            result[app_id] = (None, None, False)
            continue
        final = Decimal(overview["final"]) / 100
        initial = Decimal(overview["initial"]) / 100
        result[app_id] = (final, initial if initial != final else None, True)
    return result
