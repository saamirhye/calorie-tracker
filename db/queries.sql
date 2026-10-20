-- Daily calorie intake for a user
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