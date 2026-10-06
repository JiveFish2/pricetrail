"""Registry of the sources this deployment collects from."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from pricetrail.http import Client
from pricetrail.sources.base import Observation, Offer, Source
from pricetrail.sources.feed import AtomFeedSource
from pricetrail.sources.html import ProductPageSource
from pricetrail.sources.mercadolivre import MercadoLivreSource
from pricetrail.sources.steam import SteamSource

__all__ = ["KNOWN_SOURCES", "Observation", "Offer", "Source", "SourceInfo", "build_sources"]

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceInfo:
    id: str
    name: str
    kind: str
    homepage: str
    currency: str
    offer_url: str  # template with {id} for the external id


# Every source the catalog may reference, whether or not it can run right now.
KNOWN_SOURCES = (
    SourceInfo(
        "steam-br",
        "Steam (Brazil)",
        "api",
        "https://store.steampowered.com",
        "BRL",
        "https://store.steampowered.com/app/{id}/?cc=br",
    ),
    SourceInfo(
        "steam-us",
        "Steam (US)",
        "api",
        "https://store.steampowered.com",
        "USD",
        "https://store.steampowered.com/app/{id}/?cc=us",
    ),
    SourceInfo(
        "mercadolivre",
        "Mercado Livre",
        "api",
        "https://www.mercadolivre.com.br",
        "BRL",
        "https://produto.mercadolivre.com.br/{id}",
    ),
    SourceInfo(
        "fangamer",
        "Fangamer",
        "html",
        "https://www.fangamer.com",
        "USD",
        "https://www.fangamer.com/products/{id}",
    ),
    SourceInfo(
        "8bitdo",
        "8BitDo",
        "feed",
        "https://shop.8bitdo.com",
        "USD",
        "https://shop.8bitdo.com/products/{id}",
    ),
)

FEED_URLS = {"8bitdo": "https://shop.8bitdo.com/collections/all.atom"}


def build_sources(client: Client) -> dict[str, Source]:
    """The sources that can run in this environment, keyed by id.

    Sources that need credentials are only included when the credentials are
    present, so a developer without a Mercado Livre app can still run the rest.
    """
    sources: dict[str, Source] = {}
    for info in KNOWN_SOURCES:
        if info.id.startswith("steam-"):
            source = SteamSource(
                id=info.id,
                name=info.name,
                cc=info.id.removeprefix("steam-"),
                currency=info.currency,
                client=client,
            )
            sources[source.id] = source
        elif info.kind == "html":
            sources[info.id] = ProductPageSource(
                id=info.id,
                name=info.name,
                homepage=info.homepage,
                currency=info.currency,
                client=client,
            )
        elif info.kind == "feed":
            sources[info.id] = AtomFeedSource(
                id=info.id,
                name=info.name,
                homepage=info.homepage,
                currency=info.currency,
                feed_url=FEED_URLS[info.id],
                client=client,
            )

    client_id = os.environ.get("ML_CLIENT_ID")
    client_secret = os.environ.get("ML_CLIENT_SECRET")
    if client_id and client_secret:
        source = MercadoLivreSource(client_id=client_id, client_secret=client_secret, client=client)
        sources[source.id] = source
    else:
        log.info("mercadolivre: ML_CLIENT_ID/ML_CLIENT_SECRET not set, source disabled")
    return sources
