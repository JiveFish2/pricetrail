"""Alert notification against the local database (DATABASE_URL), in a throwaway schema."""

import os
from decimal import Decimal

import psycopg
import pytest

from pricetrail import db
from pricetrail.catalog import seed
from pricetrail.notify import DueAlert, due_alerts, money, notify, render, render_html

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")

PRODUCTS = [
    {"slug": "game-a", "name": "Game A", "category": "Games", "offers": {"steam-us": "1"}},
]


@pytest.fixture
def conn():
    connection = psycopg.connect(os.environ["DATABASE_URL"])
    connection.execute("drop schema if exists pricetrail_notify cascade")
    connection.execute("create schema pricetrail_notify")
    connection.execute("set search_path to pricetrail_notify")
    connection.commit()
    db.migrate(connection)
    seed(connection, PRODUCTS)
    yield connection
    connection.rollback()
    connection.execute("drop schema pricetrail_notify cascade")
    connection.commit()
    connection.close()


def add_price(conn, price, available=True):
    conn.execute("insert into runs (source_id, status) values ('steam-us', 'ok')")
    conn.execute(
        "insert into price_points (offer_id, run_id, price, available)"
        " values (1, (select max(id) from runs), %s, %s)",
        (price, available),
    )
    conn.commit()


def add_alert(conn, target, confirmed=True):
    conn.execute(
        "insert into alerts (offer_id, email, target_price, confirm_token, unsubscribe_token,"
        " confirmed_at) values (1, 'a@example.com', %s, 'c', 'u', %s)",
        (target, "now()" if confirmed else None),
    )
    conn.commit()


def test_alert_fires_once_when_price_reaches_target(conn, monkeypatch):
    sent = []
    monkeypatch.setattr("pricetrail.notify.send_email", lambda **kw: sent.append(kw))
    add_alert(conn, "20.00")
    add_price(conn, "25.00")
    assert notify(conn, "https://example.test") == 0

    add_price(conn, "19.99")
    assert notify(conn, "https://example.test") == 1
    assert sent[0]["to"] == "a@example.com"
    assert "https://example.test/alerts/unsubscribe/u" in sent[0]["text"]
    assert notify(conn, "https://example.test") == 0  # already notified


def test_unconfirmed_and_unavailable_do_not_fire(conn, monkeypatch):
    monkeypatch.setattr("pricetrail.notify.send_email", lambda **kw: None)
    add_alert(conn, "20.00", confirmed=False)
    add_price(conn, "10.00")
    assert due_alerts(conn) == []

    conn.execute("update alerts set confirmed_at = now()")
    add_price(conn, None, available=False)
    assert due_alerts(conn) == []


def test_send_failure_leaves_alert_pending(conn, monkeypatch):
    def boom(**kw):
        raise RuntimeError("smtp down")

    monkeypatch.setattr("pricetrail.notify.send_email", boom)
    add_alert(conn, "20.00")
    add_price(conn, "10.00")
    assert notify(conn, "https://example.test") == 0
    assert len(due_alerts(conn)) == 1


def test_money_formats_both_currencies():
    assert money(Decimal("1234.5"), "BRL") == "R$ 1.234,50"
    assert money(Decimal("1234.5"), "USD") == "$1,234.50"


def test_render_mentions_product_prices_and_links():
    text = render(
        DueAlert(
            1,
            "a@example.com",
            Decimal("20"),
            Decimal("19.99"),
            "USD",
            "Game A",
            "game-a",
            "Steam (US)",
            "https://store.test/1",
            "tok",
        ),
        "https://example.test",
    )
    assert "Game A at Steam (US) is now $19.99" in text
    assert "https://example.test/p/game-a" in text
    assert "https://example.test/alerts/unsubscribe/tok" in text


def test_render_html_escapes_and_links():
    html = render_html(
        DueAlert(
            1,
            "a@example.com",
            Decimal("20"),
            Decimal("19.99"),
            "USD",
            "Game <A>",
            "game-a",
            "Steam (US)",
            "https://store.test/1?a=1&b=2",
            "tok",
            "https://img.test/a.jpg",
        ),
        "https://example.test",
    )
    assert "Game &lt;A&gt;" in html and "Game <A>" not in html
    assert "$19.99" in html and "$20.00" in html
    assert 'href="https://store.test/1?a=1&amp;b=2"' in html
    assert 'src="https://img.test/a.jpg"' in html
    assert "https://example.test/alerts/unsubscribe/tok" in html
