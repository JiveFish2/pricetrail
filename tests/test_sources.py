import json
from decimal import Decimal
from pathlib import Path

import httpx

from pricetrail.http import Client
from pricetrail.sources.base import Offer
from pricetrail.sources.mercadolivre import parse_items
from pricetrail.sources.steam import SteamSource, parse_app_details

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


def test_steam_parses_discount_free_and_unknown():
    parsed = parse_app_details(fixture("steam_appdetails.json"))
    assert parsed["1091500"] == (Decimal("59.97"), Decimal("199.90"), True)
    assert parsed["440"] == (None, None, False)  # free to play: nothing to track
    assert parsed["999999999"] is None  # unknown app id


def test_steam_full_price_has_no_list_price():
    parsed = parse_app_details(
        {"1": {"success": True, "data": {"price_overview": {"initial": 5999, "final": 5999}}}}
    )
    assert parsed["1"] == (Decimal("59.99"), None, True)


def test_steam_fetch_batches_and_skips_unknown_ids():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        ids = request.url.params["appids"].split(",")
        body = {
            app_id: {
                "success": app_id != "0",
                "data": {"price_overview": {"initial": 1000, "final": 500}},
            }
            for app_id in ids
        }
        return httpx.Response(200, json=body)

    client = Client(pause=0, transport=httpx.MockTransport(handler))
    source = SteamSource(id="steam-us", name="Steam (US)", cc="us", currency="USD", client=client)
    offers = [Offer(i, str(i), f"https://example.test/{i}") for i in range(0, 25)]

    observations = source.fetch(offers)

    assert len(requests) == 2  # 25 ids, batches of 20
    assert requests[0].url.params["cc"] == "us"
    assert len(observations) == 24  # app "0" answered success=false
    assert observations[0].price == Decimal("5.00")
    assert observations[0].list_price == Decimal("10.00")


def test_mercadolivre_parses_active_paused_and_missing():
    parsed = parse_items(fixture("mercadolivre_items.json"))
    assert parsed["MLB1000000001"] == (Decimal("4299.9"), Decimal("4999"), True)
    assert parsed["MLB1000000002"] == (None, None, False)  # paused and out of stock
    assert parsed["MLB1000000003"] is None
