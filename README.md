# PriceTrail

A public price monitor. Every day it collects prices from several sources,
keeps the history of each offer, and (soon) emails you when a product drops
below the price you want. A status page shows whether each source is healthy,
so a broken collector never fails silently.

It is also a working example of the kind of data-extraction pipeline I build
for clients: one scraper per source, parsing tested against saved responses,
retries and rate limiting, every run recorded.

## How it works

```
catalog.toml ──seed──▶ PostgreSQL ◀──collect── sources: API (Steam, Mercado Livre)
                          │                        ▲       HTML (Fangamer)
                          │                        │       feed (8BitDo)
                          │                        └── GitHub Actions, daily cron
                          └──▶ web app + API (phase 3)
```

- **Sources** (`src/pricetrail/sources/`) implement one method, `fetch(offers)`,
  and keep parsing in pure functions so it can be tested offline.
- **Collector** (`src/pricetrail/collect.py`) runs every source, stores one
  price point per offer, and records the outcome of each run in `runs`.
- **Schema** (`migrations/`) is plain SQL applied in order by `pricetrail migrate`.
- **Scheduling** is a GitHub Actions cron (`.github/workflows/collect.yml`);
  no server to keep alive.

## Sources

| Source | Kind | Credentials |
|---|---|---|
| Steam (Brazil, US) | Public storefront JSON | none |
| Mercado Livre | Official API | `ML_CLIENT_ID` / `ML_CLIENT_SECRET` (app registered at developers.mercadolivre.com.br); skipped when absent |
| Fangamer | Product pages, schema.org microdata | none |
| 8BitDo | Atom product feed | none |

The HTML source (`sources/html.py`) reads schema.org `Product` offers from
either JSON-LD or microdata, so it works unchanged on any store that publishes
structured data. The feed source (`sources/feed.py`) reads the Shopify-style
Atom feed that many stores expose at `/collections/all.atom`.

Each run is recorded per source (status, offers read, duration, error); the
`source_status` view summarises the last run and the success rate of the past
seven days, which is what `pricetrail status` prints and the status page will show.

## Collection ethics

- Only public product data: names, prices, availability. No personal data.
- Identified `User-Agent`, one request per second, batches where the source
  allows them, and at most one run per day.
- `robots.txt` and terms of service are checked before a source is added
  (the two Shopify stores state that public product pages are crawlable).
- Failures back off exponentially; a source that keeps failing is skipped for
  the day, never retried in a loop.

## Running locally

```sh
docker compose up -d db                  # PostgreSQL on localhost:5433
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env                     # then export the variables
pricetrail migrate                       # apply migrations
pricetrail seed                          # load catalog.toml
pricetrail collect                       # fetch today's prices
pricetrail status                        # last run of each source
pytest                                   # unit + database tests
```

## Deploying the collector

1. Create a PostgreSQL database (Neon's free tier works) and run
   `pricetrail migrate` against it once.
2. Add `DATABASE_URL` (and optionally the Mercado Livre keys) as repository
   secrets.
3. The `Collect prices` workflow runs daily; trigger it manually from the
   Actions tab for the first run.

## Roadmap

- [x] Phase 1: schema, collector, Steam and Mercado Livre sources, daily cron
- [x] Phase 2: HTML and feed sources, status data
- [ ] Phase 3: web app (catalog, price charts, email alerts, read-only API)
- [ ] Phase 4: domain, documentation, case study
