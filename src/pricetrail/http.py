"""One HTTP client for every source: identified user agent, timeouts, retries
with backoff, and a pause between requests so no source is hammered."""

from __future__ import annotations

import logging
import time

import httpx

USER_AGENT = "PriceTrail/0.1 (+https://github.com/JiveFish2/pricetrail)"
RETRY_STATUSES = {429, 500, 502, 503, 504}

log = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        *,
        pause: float = 1.0,
        retries: int = 3,
        timeout: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.pause = pause
        self.retries = retries
        self._last_request = 0.0
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
        )

    def get(self, url: str, *, pause: float | None = None, **kwargs) -> httpx.Response:
        """GET with retries. `pause` overrides the client's pause for this call,
        for hosts whose robots.txt asks for a longer crawl delay."""
        delay = 2.0
        for attempt in range(1, self.retries + 1):
            self._wait_turn(self.pause if pause is None else pause)
            try:
                response = self._client.get(url, **kwargs)
            except httpx.TransportError as error:
                if attempt == self.retries:
                    raise
                log.warning("%s: %s (attempt %d), retrying", url, error, attempt)
            else:
                if response.status_code not in RETRY_STATUSES or attempt == self.retries:
                    response.raise_for_status()
                    return response
                log.warning(
                    "%s: HTTP %d (attempt %d), retrying", url, response.status_code, attempt
                )
            time.sleep(delay)
            delay *= 2
        raise AssertionError("unreachable")

    def _wait_turn(self, pause: float) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < pause:
            time.sleep(pause - elapsed)
        self._last_request = time.monotonic()

    def close(self) -> None:
        self._client.close()
