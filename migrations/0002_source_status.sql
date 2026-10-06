-- Per-source health summary for the status page and the `status` command.

create view source_status as
with recent as (
    select
        source_id,
        count(*)                                           as runs_7d,
        count(*) filter (where status = 'ok')              as ok_runs_7d,
        avg(extract(epoch from finished_at - started_at))  as avg_seconds_7d
    from runs
    where started_at > now() - interval '7 days'
      and finished_at is not null
    group by source_id
),
latest as (
    select distinct on (source_id)
        source_id, started_at, finished_at, status, offers_ok, offers_total, error
    from runs
    order by source_id, started_at desc
)
select
    s.id,
    s.name,
    s.kind,
    s.currency,
    (select count(*) from offers o where o.source_id = s.id) as offers_tracked,
    l.started_at   as last_run_at,
    l.finished_at  as last_finished_at,
    l.status       as last_status,
    l.offers_ok    as last_offers_ok,
    l.offers_total as last_offers_total,
    l.error        as last_error,
    coalesce(r.runs_7d, 0)                                            as runs_7d,
    case when r.runs_7d > 0 then round(100.0 * r.ok_runs_7d / r.runs_7d) end as ok_rate_7d,
    round(r.avg_seconds_7d::numeric, 1)                               as avg_seconds_7d
from sources s
left join latest l on l.source_id = s.id
left join recent r on r.source_id = s.id
order by s.id;
