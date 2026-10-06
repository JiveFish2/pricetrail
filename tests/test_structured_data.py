from decimal import Decimal
from pathlib import Path

from pricetrail.sources.structured_data import best_offer, parse_offers, product_image

FIXTURES = Path(__file__).parent / "fixtures"


def test_microdata_product_page():
    html = (FIXTURES / "fangamer_product.html").read_text()
    offers = parse_offers(html)

    assert len(offers) == 1
    assert offers[0].price == Decimal("32.00")
    assert offers[0].currency == "USD"
    assert offers[0].available is True


def test_json_ld_graph_picks_cheapest_in_stock_offer():
    html = (FIXTURES / "jsonld_product.html").read_text()
    offers = parse_offers(html)

    assert [offer.price for offer in offers] == [Decimal("129.00"), Decimal("139.5")]
    assert best_offer(html).price == Decimal("139.5")  # the cheaper one is out of stock


def test_microdata_text_values_and_variant_grouping():
    html = """
    <div itemprop="offers" itemscope>
      <span itemprop="price">$1,299.00</span>
      <meta itemprop="priceCurrency" content="USD">
      <link itemprop="availability" href="http://schema.org/InStock">
    </div>
    <div itemprop="offers" itemscope>
      <span itemprop="price">$999.00</span>
      <meta itemprop="priceCurrency" content="USD">
      <link itemprop="availability" href="http://schema.org/OutOfStock">
    </div>
    """
    offers = parse_offers(html)

    assert [(o.price, o.available) for o in offers] == [
        (Decimal("1299.00"), True),
        (Decimal("999.00"), False),
    ]
    assert best_offer(html).price == Decimal("1299.00")  # cheapest in stock


def test_aggregate_offer_and_price_specification():
    html = """
    <script type="application/ld+json">
    {"@type": "Product", "offers": {"@type": "AggregateOffer", "lowPrice": "45.90",
     "highPrice": "60", "priceCurrency": "BRL"}}
    </script>
    <script type="application/ld+json">
    {"@type": ["Product", "Thing"], "offers": {"@type": "Offer",
     "priceSpecification": {"price": 10}, "priceCurrency": "EUR"}}
    </script>
    <script type="application/ld+json">not json</script>
    """
    offers = parse_offers(html)

    assert [(o.price, o.currency) for o in offers] == [
        (Decimal("45.90"), "BRL"),
        (Decimal("10"), "EUR"),
    ]


def test_page_without_structured_data():
    assert parse_offers("<html><body><p>$10</p></body></html>") == []
    assert best_offer("<html></html>") is None


def test_product_image_from_microdata_resolves_protocol_relative_url():
    html = (FIXTURES / "fangamer_product.html").read_text()
    image = product_image(html)
    assert image is not None
    assert image.startswith("https://www.fangamer.com/cdn/shop/files/product_HK_knight_plush_main")


def test_product_image_from_json_ld_and_og_fallback():
    html = """
    <html><head><meta property="og:image" content="https://x.test/og.jpg"></head>
    <script type="application/ld+json">
    {"@type": "Product", "image": ["https://x.test/one.jpg", "https://x.test/two.jpg"],
     "offers": {"price": 1, "priceCurrency": "USD"}}
    </script></html>
    """
    assert product_image(html) == "https://x.test/one.jpg"
    assert (
        product_image(
            '<html><head><meta property="og:image" content="https://x.test/og.jpg"></head></html>'
        )
        == "https://x.test/og.jpg"
    )
    assert product_image("<html></html>") is None
