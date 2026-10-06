"""Mercado Livre (official API).

Since 2024 every endpoint requires an access token, so this source needs an
application registered at https://developers.mercadolivre.com.br and the
`ML_CLIENT_ID` / `ML_CLIENT_SECRET` pair in the environment. The token is
obtained with the client-credentials grant at the start of each run.

The external id is the item id (e.g. `MLB3657948929`).
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from pricetrail.http import Client
from pricetrail.sources.base import Observation, Offer

TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
ITEMS_URL = "https://api.mercadolibre.com/items"
ATTRIBUTES = "id,price,original_price,currency_id,available_quantity,status"
BATCH_SIZE = 20

log = logging.getLogger(__name__)


class MercadoLivreSource:
    id = "mercadolivre"
    name = "Mercado Livre"
    kind = "api"
    homepage = "https://www.mercadolivre.com.br"
    currency = "BRL"

    def __init__(self, *, client_id: str, client_secret: str, client: Client) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.client = client

    def fetch(self, offers: list[Offer]) -> list[Observation]:
        token = self._access_token()
        by_external = {offer.external_id: offer for offer in offers}
        observations: list[Observation] = []
        ids = list(by_external)
        for start in range(0, len(ids), BATCH_SIZE):
            batch = ids[start : start + BATCH_SIZE]
            response = self.client.get(
                ITEMS_URL,
                params={"ids": ",".join(batch), "attributes": ATTRIBUTES},
                headers={"Authorization": f"Bearer {token}"},
            )
            for external_id, parsed in parse_items(response.json()).items():
                offer = by_external.get(external_id)
                if offer is None:
                    continue
                if parsed is None:
                    log.warning("%s: item %s not found, skipping", self.id, external_id)
                    continue
                price, list_price, available = parsed
                observations.append(Observation(offer.id, price, list_price, available))
        return observations

    def _access_token(self) -> str:
        response = self.client._client.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]


def parse_items(
    payload: list[dict[str, Any]],
) -> dict[str, tuple[Decimal | None, Decimal | None, bool] | None]:
    """Map item id -> (price, list_price, available), or None when the item is unknown.

    The multiget endpoint answers a list of `{code, body}` envelopes; an item that
    is paused or closed still has a price, but we record it as unavailable.
    """
    result: dict[str, tuple[Decimal | None, Decimal | None, bool] | None] = {}
    for envelope in payload:
        body = envelope.get("body") or {}
        if envelope.get("code") != 200:
            item_id = body.get("id") or _id_from_error(body)
            if item_id:
                result[item_id] = None
            continue
        item_id = body["id"]
        available = body.get("status") == "active" and (body.get("available_quantity") or 0) > 0
        price = Decimal(str(body["price"])) if body.get("price") is not None else None
        original = body.get("original_price")
        list_price = Decimal(str(original)) if original is not None and price is not None else None
        if list_price is not None and list_price <= price:
            list_price = None
        result[item_id] = (
            price if available else None,
            list_price if available else None,
            available,
        )
    return result


def _id_from_error(body: dict[str, Any]) -> str | None:
    # Error bodies look like {"message": "Item with id MLB123 not found", ...}.
    for word in str(body.get("message", "")).split():
        if word.startswith("ML") and word[2:].isalnum():
            return word
    return None
