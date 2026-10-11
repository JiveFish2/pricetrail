from decimal import Decimal
from pathlib import Path

import httpx

from pricetrail.http import Client
from pricetrail.sources.base import Offer
from pricetrail.sources.feed import AtomFeedSource, parse_feed
from pricetrail.sources.html import ProductPageSource

FIXTURES = Path(__file__).parent / "fixtures"


def test_feed_maps_product_id_to_lowest_variant_price():
    prices = parse_feed((FIXTURES / "shopify_feed.atom").read_text(), currency="USD")

    assert prices["9034781687985"][0] == Decimal("149.99")
    assert prices["7488962724017"][0] == Decimal("0.71")  # several variants, lowest wins
    assert prices["9071189131441"][0] == Decimal("29.99")
    assert prices["9034781687985"][1].startswith("https://cdn.shopify.com/")


def test_feed_ignores_other_currencies():
    prices = parse_feed((FIXTURES / "shopify_feed.atom").read_text(), currency="BRL")
    assert prices == {}


def test_feed_source_skips_products_missing_from_the_feed():
    feed = (FIXTURES / "shopify_feed.atom").read_text()
    client = Client(
        pause=0, transport=httpx.MockTransport(lambda _: httpx.Response(200, text=feed))
    )
    source = AtomFeedSource(
        id="8bitdo",
        name="8BitDo",
        homepage="https://shop.8bitdo.com",
        currency="USD",
        feed_url="https://shop.8bitdo.com/all.atom",
        client=client,
    )
    offers = [Offer(1, "9034781687985", "u1"), Offer(2, "0000", "u2")]

    observations = source.fetch(offers)

    assert [(o.offer_id, o.price, o.available) for o in observations] == [
        (1, Decimal("149.99"), True)
    ]


def test_html_source_reads_each_page_and_skips_gone_pages():
    page = (FIXTURES / "fangamer_product.html").read_text()
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        if request.url.path.endswith("/gone"):
            return httpx.Response(404)
        if request.url.path.endswith("/blank"):
            return httpx.Response(200, text="<html><body>no data</body></html>")
        return httpx.Response(200, text=page)

    client = Client(pause=0, transport=httpx.MockTransport(handler))
    source = ProductPageSource(
        id="fangamer",
        name="Fangamer",
        homepage="https://example.test",
        currency="USD",
        client=client,
    )
    offers = [
        Offer(1, "plush", "https://example.test/products/plush"),
        Offer(2, "gone", "https://example.test/products/gone"),
        Offer(3, "blank", "https://example.test/products/blank"),
    ]

    observations = source.fetch(offers)

    assert seen == ["/products/plush", "/products/gone", "/products/blank"]
    assert [(o.offer_id, o.price, o.available) for o in observations] == [
        (1, Decimal("32.00"), True)
    ]


def test_html_source_skips_pages_priced_in_another_currency():
    page = (FIXTURES / "fangamer_product.html").read_text()
    client = Client(
        pause=0, transport=httpx.MockTransport(lambda _: httpx.Response(200, text=page))
    )
    source = ProductPageSource(
        id="x", name="X", homepage="https://example.test", currency="BRL", client=client
    )

    assert source.fetch([Offer(1, "plush", "https://example.test/p")]) == []


def test_html_source_passes_the_store_crawl_delay_to_the_client():
    page = (FIXTURES / "fangamer_product.html").read_text()
    pauses: list[float | None] = []

    class RecordingClient(Client):
        def get(self, url, *, pause=None, **kwargs):
            pauses.append(pause)
            return super().get(url, pause=0, **kwargs)

    client = RecordingClient(
        pause=0, transport=httpx.MockTransport(lambda _: httpx.Response(200, text=page))
    )
    source = ProductPageSource(
        id="x", name="X", homepage="https://example.test", currency="USD", client=client, pause=10.0
    )

    source.fetch([Offer(1, "a", "https://example.test/a"), Offer(2, "b", "https://example.test/b")])

    assert pauses == [10.0, 10.0]
