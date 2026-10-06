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
                          │                            (collect → notify → revalidate site)
                          └──▶ web/ (Next.js): catalog, price charts, status, JSON API, alerts
```

- **Sources** (`src/pricetrail/sources/`) implement one method, `fetch(offers)`,
  and keep parsing in pure functions so it can be tested offline.
- **Collector** (`src/pricetrail/collect.py`) runs every source, stores one
  price point per offer, and records the outcome of each run in `runs`.
- **Schema** (`migrations/`) is plain SQL applied in order by `pricetrail migrate`.
- **Alerts** (`src/pricetrail/notify.py`) run after each collection: every
  confirmed alert whose target was reached gets one email, then stays marked.
- **Scheduling** is a GitHub Actions cron (`.github/workflows/collect.yml`);
  no server to keep alive.
- **Site** (`web/`) is a Next.js app that reads the same database: catalog,
  per-product history chart and 30-day range, status page built on the
  `source_status` view, a read-only JSON API, and the alert form (email
  confirmed by link, removed by link, no accounts).

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

## Running the site

```sh
cd web
npm install
cp .env.example .env.local                # DATABASE_URL, RESEND_API_KEY, REVALIDATE_SECRET…
npm run dev -- -p 3001
```

Pages and API responses are cached for an hour; the collector workflow calls
`POST /api/revalidate` with the shared secret after each run so new prices show
up right away. Without `RESEND_API_KEY` the emails are printed to the server log.

## Deploying the collector

1. Create a PostgreSQL database (Neon's free tier works) and run
   `pricetrail migrate` against it once.
2. Add `DATABASE_URL`, `RESEND_API_KEY` and `REVALIDATE_SECRET` (and optionally
   the Mercado Livre keys) as repository secrets, and `SITE_URL` / `ALERT_FROM`
   as repository variables.
3. Deploy `web/` to Vercel with the same `DATABASE_URL`, `RESEND_API_KEY`,
   `REVALIDATE_SECRET`, `ALERT_FROM` and `NEXT_PUBLIC_SITE_URL`.
4. The `Collect prices` workflow runs daily; trigger it manually from the
   Actions tab for the first run.

## Roadmap

- [x] Phase 1: schema, collector, Steam and Mercado Livre sources, daily cron
- [x] Phase 2: HTML and feed sources, status data
- [x] Phase 3: web app (catalog, price charts, email alerts, read-only API)
- [ ] Phase 4: domain, documentation, case study
