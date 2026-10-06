"""The contract every source implements.

A source receives the offers it is responsible for and returns one observation
per offer it managed to read. Parsing is kept in pure functions (`parse_*`) so
it can be tested against saved responses without network access.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class Offer:
    id: int
    external_id: str
    url: str


@dataclass(frozen=True)
class Observation:
    offer_id: int
    price: Decimal | None  # None when the product is not for sale right now
    list_price: Decimal | None
    available: bool


class Source(Protocol):
    id: str
    name: str
    kind: str  # 'api' | 'html' | 'feed'
    homepage: str
    currency: str

    def fetch(self, offers: list[Offer]) -> list[Observation]:
        """Return observations for the offers that could be read.

        Raise for failures that affect the whole run (network down, auth
        rejected); skip individual offers that cannot be read.
        """
        ...
