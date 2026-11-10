-- Daily calorie intake with running totals
with logged as (
	select (e.consumed_at at time zone e.timezone)::date as tracked_day,
	       e.calories * e.servings as kcal,
	       e.protein * e.servings as protein,
	       e.carbs * e.servings as carbs,
	       e.fat * e.servings as fats
	from entries e
	join users u on e.user_id = u.id
	where u.username = 'greg' and e.deleted_at is null
)
, daily as (
    select tracked_day, count(*) as entries, sum(kcal) as kcal, sum(protein) as protein, sum(carbs) as carbs, sum(fats) as fats
    from logged
    group by tracked_day
)
select to_char(tracked_day, 'FMDD Mon') as day,
        entries,
        round(kcal, 1) as k_cal,
        round(sum(kcal) over (order by tracked_day), 1) as run_kcal,
        round(sum(protein) over (order by tracked_day), 1) as run_protein,
        round(sum(carbs) over (order by tracked_day), 1) as run_carbs,
        round(sum(fats) over (order by tracked_day), 1) as run_fats
from daily
order by tracked_day;

-- Week view metrics
with logged as(
  select (e.consumed_at at time zone e.timezone)::date as tracked_day,
          (e.calories * e.servings) as kcal,
          (e.protein * e.servings) as protein,
          (e.carbs * e.servings) as carbs,
          (e.fat * e.servings) as fats
  from entries e
  join users u on e.user_id = u.id
  where u.username = 'Greg' and e.deleted_at is null
)
, daily as (
  select tracked_day,
          count(*) as entries,
          sum(kcal) as kcal,
          sum(protein) as protein,
          sum(carbs) as carbs,
          sum(fats) as fats
  from logged
  group by tracked_day
)
, params as (select '2026-10-19'::date as week_start)
, days as (
  select d::date as day_date
  from params,
      generate_series(params.week_start,
                      params.week_start + 6, interval '1 day') as d
)
select days.day_date,
        to_char(days.day_date, 'Dy') as day,
        coalesce(daily.entries, 0) as entries,
        coalesce(round(daily.kcal, 1), 0) as kcal,
        coalesce(round(daily.protein, 1), 0) as protein,
        coalesce(round(daily.carbs, 1), 0) as carbs,
        coalesce(round(daily.fats, 1), 0) as fats
from days
left join daily on daily.tracked_day = days.day_date
order by days.day_date;

-- Todays metrics in order
with params as (select '2026-10-21'::date as selected_date)
select to_char(e.consumed_at at time zone e.timezone, 'HH24:MI') as local_time,
        e.food_name as food_name,
        e.servings as servings,
        round(e.calories * e.servings, 1) as kcal
from entries e
join users u on e.user_id = u.id
join params p on p.selected_date = (e.consumed_at at time zone e.timezone)::date
where u.username = 'Greg' and e.deleted_at is null
order by e.consumed_at;


-- Remaining targets
-- Add `explain (analyze, buffers)` in front to see the plan. Timings are in db/perf/results.md.
with params as (
  select u.id as user_id, '2026-10-18'::date as week_start
  from users u
  where u.username = 'Greg'
)
, logged as (
  select (e.consumed_at at time zone e.timezone)::date as day,
        (e.calories * e.servings) as eaten
  from entries e
  join params p on e.user_id = p.user_id
  where e.deleted_at is null
        -- Compare the raw column so entries_user_consumed_at_idx can be used.
        -- The window is a day wider each side because days are local and
        -- consumed_at is UTC. The join to days trims the extras.
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
