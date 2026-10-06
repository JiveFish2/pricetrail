"""Command line entry point: `pricetrail migrate | seed | collect | notify | status`."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from pricetrail import db
from pricetrail.catalog import load_catalog, seed
from pricetrail.collect import collect
from pricetrail.http import Client
from pricetrail.notify import notify
from pricetrail.sources import build_sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pricetrail")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="apply pending SQL migrations")
    sub.add_parser("seed", help="upsert catalog.toml into the database")
    run = sub.add_parser("collect", help="collect prices from every enabled source")
    run.add_argument("--source", action="append", help="limit to this source id (repeatable)")
    sub.add_parser("notify", help="email confirmed alerts whose target price was reached")
    sub.add_parser("status", help="print the latest run of each source")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    with db.connect() as conn:
        if args.command == "migrate":
            applied = db.migrate(conn)
            print("applied:", ", ".join(applied) if applied else "nothing to do")
        elif args.command == "seed":
            products, offers = seed(conn, load_catalog())
            print(f"seeded {products} products, {offers} offers")
        elif args.command == "collect":
            client = Client()
            try:
                results = collect(conn, build_sources(client), set(args.source or []))
            finally:
                client.close()
            for r in results:
                line = f"{r.source_id:<14} {r.status:<8} {r.offers_ok}/{r.offers_total}"
                print(line + (f"  {r.error}" if r.error else ""))
            return 0 if all(r.status == "ok" for r in results) else 1
        elif args.command == "notify":
            site_url = os.environ.get("SITE_URL", "http://localhost:3001").rstrip("/")
            print(f"sent {notify(conn, site_url)} alert emails")
        elif args.command == "status":
            with conn.cursor() as cur:
                cur.execute(
                    "select id, kind, last_status, last_offers_ok, last_offers_total,"
                    " last_run_at, avg_seconds_7d, ok_rate_7d, runs_7d, last_error"
                    " from source_status"
                )
                rows = cur.fetchall()
            print(f"{'source':<14} {'kind':<5} {'last run':<24} {'7 days':<14} error")
            for id, kind, status, ok, total, at, seconds, rate, runs, error in rows:
                last = (
                    f"{status} {ok}/{total} {at:%m-%d %H:%M} {seconds or 0}s"
                    if status
                    else "never ran"
                )
                week = f"{rate}% of {runs}" if runs else "-"
                print(f"{id:<14} {kind:<5} {last:<24} {week:<14} {error or ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
