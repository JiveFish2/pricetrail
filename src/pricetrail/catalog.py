"""Loads catalog.toml and upserts sources, products and offers into the database."""

from __future__ import annotations

import tomllib
from pathlib import Path

import psycopg

from pricetrail.sources import KNOWN_SOURCES

CATALOG_PATH = Path(__file__).resolve().parents[2] / "catalog.toml"


def load_catalog(path: Path = CATALOG_PATH) -> list[dict]:
    with path.open("rb") as file:
        return tomllib.load(file)["products"]


def seed(conn: psycopg.Connection, products: list[dict]) -> tuple[int, int]:
    """Upsert every known source, then the products and their offers.

    Returns (products, offers) written.
    """
    by_id = {info.id: info for info in KNOWN_SOURCES}
    offers_written = 0
    with conn.cursor() as cur:
        for info in KNOWN_SOURCES:
            cur.execute(
                "insert into sources (id, name, kind, homepage, currency)"
                " values (%s, %s, %s, %s, %s)"
                " on conflict (id) do update set name = excluded.name, kind = excluded.kind,"
                " homepage = excluded.homepage, currency = excluded.currency",
                (info.id, info.name, info.kind, info.homepage, info.currency),
            )
        for product in products:
            cur.execute(
                "insert into products (slug, name, category, image_url)"
                " values (%(slug)s, %(name)s, %(category)s, %(image_url)s)"
                " on conflict (slug) do update set name = excluded.name,"
                " category = excluded.category,"
                " image_url = coalesce(products.image_url, excluded.image_url)"
                " returning id",
                {"image_url": None, **product},
            )
            product_id = cur.fetchone()[0]
            for source_id, external_id in product["offers"].items():
                info = by_id.get(source_id)
                if info is None:
                    raise SystemExit(f"{product['slug']}: unknown source {source_id!r}")
                cur.execute(
                    "insert into offers (product_id, source_id, external_id, url)"
                    " values (%s, %s, %s, %s)"
                    " on conflict (product_id, source_id) do update"
                    " set external_id = excluded.external_id, url = excluded.url",
                    (
                        product_id,
                        source_id,
                        str(external_id),
                        info.offer_url.format(id=external_id),
                    ),
                )
                offers_written += 1
    conn.commit()
    return len(products), offers_written
