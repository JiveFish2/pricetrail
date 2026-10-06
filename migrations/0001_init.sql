-- PriceTrail core schema.
-- A product is sold by several sources; each (product, source) pair is an offer,
-- and every collection run appends one price point per offer.

create table sources (
    id          text primary key,            -- e.g. 'steam-br'
    name        text not null,               -- e.g. 'Steam (Brazil)'
    kind        text not null check (kind in ('api', 'html', 'feed')),
    homepage    text not null,
    currency    char(3) not null
);

create table products (
    id          serial primary key,
    slug        text not null unique,
    name        text not null,
    category    text not null,
    image_url   text,
    created_at  timestamptz not null default now()
);

create table offers (
    id          serial primary key,
    product_id  integer not null references products (id) on delete cascade,
    source_id   text not null references sources (id),
    external_id text not null,               -- the source's own identifier for the product
    url         text not null,
    created_at  timestamptz not null default now(),
    unique (source_id, external_id),
    unique (product_id, source_id)
);

-- One row per source per collection run: the data behind the status page.
create table runs (
    id            serial primary key,
    source_id     text not null references sources (id),
    started_at    timestamptz not null default now(),
    finished_at   timestamptz,
    status        text not null default 'running'
                  check (status in ('running', 'ok', 'partial', 'failed')),
    offers_total  integer not null default 0,
    offers_ok     integer not null default 0,
    error         text
);

create index runs_source_started_idx on runs (source_id, started_at desc);

create table price_points (
    id          bigserial primary key,
    offer_id    integer not null references offers (id) on delete cascade,
    run_id      integer not null references runs (id) on delete cascade,
    price       numeric(12, 2),              -- null when the offer is unavailable
    list_price  numeric(12, 2),              -- price before discount, when the source gives one
    available   boolean not null,
    observed_at timestamptz not null default now()
);

create index price_points_offer_observed_idx on price_points (offer_id, observed_at desc);
