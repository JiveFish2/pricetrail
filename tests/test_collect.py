"""Collector tests against a real PostgreSQL (DATABASE_URL), in a throwaway schema."""

import os
from decimal import Decimal

import psycopg
import pytest

from pricetrail import db
from pricetrail.catalog import seed
from pricetrail.collect import collect
from pricetrail.sources.base import Observation, Offer

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")

PRODUCTS = [
    {
        "slug": "game-a",
        "name": "Game A",
        "category": "Games",
        "offers": {"steam-br": "1", "steam-us": "1"},
    },
    {"slug": "game-b", "name": "Game B", "category": "Games", "offers": {"steam-br": "2"}},
]


class FakeSource:
    kind = "api"
    homepage = "https://example.test"

    def __init__(self, id: str, currency: str, *, fail: bool = False, drop: str | None = None):
        self.id = id
        self.name = id
        self.currency = currency
        self.fail = fail
        self.drop = drop
        self.seen: list[Offer] = []

    def fetch(self, offers: list[Offer]) -> list[Observation]:
        self.seen = offers
        if self.fail:
            raise ConnectionError("boom")
        return [
            Observation(o.id, Decimal("10.00"), None, True)
            for o in offers
            if o.external_id != self.drop
        ]


@pytest.fixture
def conn():
    connection = psycopg.connect(os.environ["DATABASE_URL"])
    connection.execute("drop schema if exists pricetrail_test cascade")
    connection.execute("create schema pricetrail_test")
    connection.execute("set search_path to pricetrail_test")
    connection.commit()
    db.migrate(connection)
    seed(connection, PRODUCTS)
    yield connection
    connection.rollback()
    connection.execute("drop schema pricetrail_test cascade")
    connection.commit()
    connection.close()


def test_seed_is_idempotent(conn):
    seed(conn, PRODUCTS)
    assert conn.execute("select count(*) from products").fetchone()[0] == 2
    assert conn.execute("select count(*) from offers").fetchone()[0] == 3


def test_each_source_gets_its_own_offers_and_a_run_row(conn):
    br, us = FakeSource("steam-br", "BRL"), FakeSource("steam-us", "USD")

    results = collect(conn, {"steam-br": br, "steam-us": us})

    assert [o.external_id for o in br.seen] == ["1", "2"]
    assert [o.external_id for o in us.seen] == ["1"]
    assert [(r.source_id, r.status, r.offers_ok, r.offers_total) for r in results] == [
        ("steam-br", "ok", 2, 2),
        ("steam-us", "ok", 1, 1),
    ]
    assert conn.execute("select count(*) from price_points").fetchone()[0] == 3
    assert (
        conn.execute("select count(*) from runs where finished_at is not null").fetchone()[0] == 2
    )


def test_failed_source_is_recorded_and_does_not_stop_the_others(conn):
    results = collect(
        conn,
        {
            "steam-br": FakeSource("steam-br", "BRL", fail=True),
            "steam-us": FakeSource("steam-us", "USD"),
        },
    )

    assert results[0].status == "failed"
    assert results[0].error == "ConnectionError: boom"
    assert results[1].status == "ok"
    assert conn.execute(
        "select status, error from runs where source_id = 'steam-br'"
    ).fetchone() == ("failed", "ConnectionError: boom")


def test_partial_run_when_an_offer_is_missing(conn):
    results = collect(conn, {"steam-br": FakeSource("steam-br", "BRL", drop="2")})

    assert (results[0].status, results[0].offers_ok, results[0].error) == (
        "partial",
        1,
        "1 of 2 offers not read",
    )


def test_only_filter_limits_the_sources(conn):
    br, us = FakeSource("steam-br", "BRL"), FakeSource("steam-us", "USD")

    results = collect(conn, {"steam-br": br, "steam-us": us}, only={"steam-us"})

    assert [r.source_id for r in results] == ["steam-us"]
    assert br.seen == []
