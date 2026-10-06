"""One collection run: for each source, read its offers, store a price point per
observation, and record the outcome in `runs`.

A source failing never stops the others. The run row is written before the
source starts, so a crash still leaves a 'running' row the status page can flag.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import psycopg

from pricetrail.sources import Offer, Source

log = logging.getLogger(__name__)


@dataclass
class RunResult:
    source_id: str
    status: str
    offers_total: int
    offers_ok: int
    error: str | None = None


def collect(
    conn: psycopg.Connection, sources: dict[str, Source], only: set[str] | None = None
) -> list[RunResult]:
    results: list[RunResult] = []
    for source_id, source in sources.items():
        if only and source_id not in only:
            continue
        results.append(collect_source(conn, source))
    return results


def collect_source(conn: psycopg.Connection, source: Source) -> RunResult:
    offers = load_offers(conn, source.id)
    with conn.cursor() as cur:
        cur.execute(
            "insert into runs (source_id, offers_total) values (%s, %s) returning id",
            (source.id, len(offers)),
        )
        run_id = cur.fetchone()[0]
    conn.commit()

    try:
        observations = source.fetch(offers)
    except Exception as error:  # noqa: BLE001 - any failure is recorded, not raised
        log.exception("%s: run failed", source.id)
        return _finish(
            conn,
            run_id,
            RunResult(source.id, "failed", len(offers), 0, f"{type(error).__name__}: {error}"),
        )

    with conn.cursor() as cur:
        cur.executemany(
            "insert into price_points (offer_id, run_id, price, list_price, available)"
            " values (%s, %s, %s, %s, %s)",
            [(o.offer_id, run_id, o.price, o.list_price, o.available) for o in observations],
        )
        cur.executemany(
            "update products set image_url = %s"
            " where image_url is null and id = (select product_id from offers where id = %s)",
            [(o.image_url, o.offer_id) for o in observations if o.image_url],
        )
    ok = len(observations)
    status = "ok" if ok == len(offers) else ("partial" if ok else "failed")
    error = None if status == "ok" else f"{len(offers) - ok} of {len(offers)} offers not read"
    return _finish(conn, run_id, RunResult(source.id, status, len(offers), ok, error))


def load_offers(conn: psycopg.Connection, source_id: str) -> list[Offer]:
    with conn.cursor() as cur:
        cur.execute(
            "select id, external_id, url from offers where source_id = %s order by id",
            (source_id,),
        )
        return [Offer(*row) for row in cur.fetchall()]


def _finish(conn: psycopg.Connection, run_id: int, result: RunResult) -> RunResult:
    with conn.cursor() as cur:
        cur.execute(
            "update runs set finished_at = now(), status = %s, offers_ok = %s, error = %s"
            " where id = %s",
            (result.status, result.offers_ok, result.error, run_id),
        )
    conn.commit()
    log.info(
        "%s: %s (%d/%d offers)",
        result.source_id,
        result.status,
        result.offers_ok,
        result.offers_total,
    )
    return result
