import httpx
import pytest

from pricetrail.http import USER_AGENT, Client


def test_retries_server_errors_then_succeeds(monkeypatch):
    monkeypatch.setattr("pricetrail.http.time.sleep", lambda _: None)
    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(request.headers["user-agent"])
        return httpx.Response(503 if len(attempts) < 3 else 200, json={"ok": True})

    client = Client(pause=0, transport=httpx.MockTransport(handler))
    response = client.get("https://example.test/")

    assert response.json() == {"ok": True}
    assert attempts == [USER_AGENT] * 3


def test_gives_up_after_last_retry(monkeypatch):
    monkeypatch.setattr("pricetrail.http.time.sleep", lambda _: None)
    client = Client(
        pause=0, retries=2, transport=httpx.MockTransport(lambda _: httpx.Response(503))
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.get("https://example.test/")


def test_client_errors_are_not_retried():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(404)

    client = Client(pause=0, transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        client.get("https://example.test/")
    assert calls == 1


def test_pause_per_call_overrides_the_client_pause(monkeypatch):
    waits: list[float] = []
    clock = iter(range(0, 1000, 1))
    monkeypatch.setattr("pricetrail.http.time.monotonic", lambda: float(next(clock)))
    monkeypatch.setattr("pricetrail.http.time.sleep", waits.append)
    client = Client(pause=1.0, transport=httpx.MockTransport(lambda _: httpx.Response(200)))

    client.get("https://example.test/a")
    client.get("https://example.test/b", pause=10.0)

    # The clock advances one second per reading: 1s before the first call, then
    # the second call tops the gap up to the 10s crawl delay.
    assert waits == [1.0, 9.0]
