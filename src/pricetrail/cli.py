"""Command line entry point: `pricetrail migrate | seed | collect | status`."""

from __future__ import annotations

import argparse
import logging
import sys

from pricetrail import db
from pricetrail.catalog import load_catalog, seed
from pricetrail.collect import collect
from pricetrail.http import Client
from pricetrail.sources import build_sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pricetrail")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="apply pending SQL migrations")
    sub.add_parser("seed", help="upsert catalog.toml into the database")
    run = sub.add_parser("collect", help="collect prices from every enabled source")
    run.add_argument("--source", action="append", help="limit to this source id (repeatable)")
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
        elif args.command == "status":
            with conn.cursor() as cur:
                cur.execute(
                    "select distinct on (source_id) source_id, status, started_at, finished_at,"
                    " offers_ok, offers_total, error from runs"
                    " order by source_id, started_at desc"
                )
                rows = cur.fetchall()
            if not rows:
                print("no runs yet")
            for source_id, status, started, finished, ok, total, error in rows:
                took = f"{(finished - started).total_seconds():.1f}s" if finished else "running"
                print(
                    f"{source_id:<14} {status:<8} {ok}/{total:<4} {started:%Y-%m-%d %H:%M} "
                    f"{took}" + (f"  {error}" if error else "")
                )
    return 0


if __name__ == "__main__":
    sys.exit(main())
