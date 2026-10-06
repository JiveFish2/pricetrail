-- Email alerts: "tell me when this offer goes at or below target_price".
-- No accounts: the address is confirmed by a link, and every email carries an
-- unsubscribe link. An alert fires once (notified_at) and then stays for history.

create table alerts (
    id                serial primary key,
    offer_id          integer not null references offers (id) on delete cascade,
    email             text not null,
    target_price      numeric(12, 2) not null check (target_price > 0),
    confirm_token     text not null unique,
    unsubscribe_token text not null unique,
    confirmed_at      timestamptz,
    notified_at       timestamptz,
    created_at        timestamptz not null default now(),
    unique (offer_id, email)
);

create index alerts_pending_idx on alerts (offer_id)
    where confirmed_at is not null and notified_at is null;
