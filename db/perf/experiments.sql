-- Index experiments for the weekly remaining-calories report. Results are in results.md.
-- Run on tracker_perf (see generate_entries.sql), never on the dev database.

-- Tried first: finds a user's rows, but still reads their whole history.
-- create index entries_user_idx on entries (user_id);
-- drop index entries_user_idx;

-- Kept (migration 0002): user and date range in one lookup. It also covers user_id alone.
create index entries_user_consumed_at_idx on entries (user_id, consumed_at);

select indexname, indexdef
from pg_indexes
where tablename = 'entries';

-- The report with the week window. Run it five times and use the median execution time.
explain (analyze, buffers)
with params as (
  select u.id as user_id, '2026-10-12'::date as week_start
  from users u
  where u.username = 'perf_user_1'
)
, logged as (
  select (e.consumed_at at time zone e.timezone)::date as day,
        (e.calories * e.servings) as eaten
  from entries e
  join params p on e.user_id = p.user_id
  where e.deleted_at is null
        and e.consumed_at >= (week_start - 1)
        and e.consumed_at < (week_start + 8)
)
, daily as (
  select day,
        sum(eaten) as eaten
  from logged
  group by day
)
, days as (
  select d::date as day_date, params.user_id
  from params,
      generate_series(params.week_start,
                      params.week_start + 6, interval '1 day') as d
)
select to_char(d.day_date, 'FMDD Mon') as day,
      t.target_value as target,
      coalesce(daily.eaten, 0) as eaten,
      (t.target_value - coalesce(daily.eaten, 0)) as remaining
from days d
left join targets t on t.start_date <= d.day_date
      and (t.end_date is null or t.end_date >= d.day_date)
      and t.target_type = 'calories' and t.deleted_at is null
      and t.user_id = d.user_id
left join daily on daily.day = d.day_date
order by d.day_date;
