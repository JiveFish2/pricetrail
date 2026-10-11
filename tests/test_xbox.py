from decimal import Decimal
from pathlib import Path

import httpx

from pricetrail.http import Client
from pricetrail.sources.base import Offer
from pricetrail.sources.xbox import XboxSource, parse_product_page

PAGE = (Path(__file__).parent / "fixtures" / "xbox_product_state.html").read_text()


def test_xbox_reads_a_pre_order():
    price, list_price, currency, image = parse_product_page(PAGE, "9P3H4968GRSM")
    assert (price, list_price, currency) == (Decimal("79.99"), None, "USD")
    assert image.startswith("https://store-images.s-microsoft.com/image/")


def test_xbox_sale_keeps_the_regular_price_as_list_price():
    price, list_price, currency, _ = parse_product_page(PAGE, "9NLLTTJZH40L")
    assert (price, list_price, currency) == (Decimal("17.49"), Decimal("34.99"), "USD")


def test_xbox_ignores_the_game_pass_member_price():
    # Stardew Valley also lists $11.99 for Game Pass members; everyone else pays $14.99.
    price, list_price, _, _ = parse_product_page(PAGE, "C3D891Z6TNQM")
    assert (price, list_price) == (Decimal("14.99"), None)


def test_xbox_unknown_product_or_page_without_state():
    assert parse_product_page(PAGE, "0000000000") is None
    assert parse_product_page("<html><body>maintenance</body></html>", "C3D891Z6TNQM") is None


def test_xbox_source_skips_gone_and_other_currency_pages():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/GONE"):
            return httpx.Response(404)
        return httpx.Response(200, text=PAGE)

    client = Client(pause=0, transport=httpx.MockTransport(handler))
    us = XboxSource(id="xbox-us", name="Xbox Store (US)", currency="USD", client=client)
    br = XboxSource(id="xbox-br", name="Xbox Store (Brazil)", currency="BRL", client=client)
    offers = [
        Offer(1, "9NLLTTJZH40L", "https://example.test/p/9NLLTTJZH40L"),
        Offer(2, "GONE", "https://example.test/p/GONE"),
    ]

    assert [(o.offer_id, o.price, o.list_price) for o in us.fetch(offers)] == [
        (1, Decimal("17.49"), Decimal("34.99"))
    ]
    assert br.fetch(offers) == []  # the fixture is priced in USD
