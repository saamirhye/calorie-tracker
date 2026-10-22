"""Time the weekly remaining-calories report under different indexes.

Run only against the tracker_perf database (see generate_entries.sql). It drops and
creates indexes on entries, then leaves entries_user_consumed_at_idx in place.

Each version runs six times. The first run is discarded and the median of the other
five is reported, with the scan type, rows read and buffers from the first plan, and a
checksum of the report output to confirm every version returns the same answer.
"""

import hashlib
import json
import re
import statistics
import subprocess

PSQL = [
    "docker", "exec", "-i", "calorie-tracker-db-1",
    "psql", "-U", "tracker", "-d", "tracker_perf", "-X", "-q", "-v", "ON_ERROR_STOP=1",
]  # fmt: skip

REPORT = """with params as (
  select u.id as user_id, '2026-10-12'::date as week_start
  from users u where u.username = 'perf_user_1'
)
, logged as (
  select (e.consumed_at at time zone e.timezone)::date as day,
         (e.calories * e.servings) as eaten
  from entries e join params p on e.user_id = p.user_id
  where e.deleted_at is null{window}
)
, daily as (select day, sum(eaten) as eaten from logged group by day)
, days as (
  select d::date as day_date, params.user_id
  from params,
       generate_series(params.week_start, params.week_start + 6, interval '1 day') as d
)
select to_char(d.day_date, 'FMDD Mon') as day, t.target_value as target,
       coalesce(daily.eaten, 0) as eaten,
       (t.target_value - coalesce(daily.eaten, 0)) as remaining
from days d
left join targets t on t.start_date <= d.day_date
      and (t.end_date is null or t.end_date >= d.day_date)
      and t.target_type = 'calories' and t.deleted_at is null and t.user_id = d.user_id
left join daily on daily.day = d.day_date
order by d.day_date;
"""
WEEK_WINDOW = """
        and e.consumed_at >= (week_start - 1)
        and e.consumed_at < (week_start + 8)"""
RUNS = 6


def psql(sql: str, tuples_only: bool = True) -> str:
    args = PSQL + (["-At"] if tuples_only else [])
    result = subprocess.run(
        args, check=False, input=sql, capture_output=True, text=True
    )
    if result.returncode:
        raise SystemExit(result.stderr)
    return result.stdout


def report(with_window: bool) -> str:
    return REPORT.format(window=WEEK_WINDOW if with_window else "")


def measure(label: str, with_window: bool) -> dict[str, object]:
    plans = [
        psql("explain (analyze, buffers) " + report(with_window), tuples_only=False)
        for _ in range(RUNS)
    ]
    times = [
        float(re.search(r"Execution Time: ([\d.]+) ms", p).group(1)) for p in plans[1:]
    ]  # type: ignore[union-attr]
    first = plans[0].splitlines()
    scan_line = next(line.strip() for line in first if " on entries" in line)
    buffers = next(line for line in first if "Buffers:" in line).split(
        "Buffers: shared "
    )[1]
    return {
        "version": label,
        "median_ms": statistics.median(times),
        "runs_ms": times,
        "entries_scan": scan_line.split("  (")[0].removeprefix("-> "),
        "rows_read": int(re.search(r"actual time=\S+ rows=(\d+)", scan_line).group(1)),  # type: ignore[union-attr]
        "buffers": buffers,
        "output_checksum": hashlib.md5(psql(report(with_window)).encode()).hexdigest()[
            :8
        ],
    }


def main() -> None:
    results = []
    psql(
        "drop index if exists entries_user_idx; drop index if exists entries_user_consumed_at_idx;"
    )
    results.append(measure("no index, no week window", False))
    psql("create index entries_user_idx on entries (user_id);")
    results.append(measure("user_id index, no week window", False))
    psql("drop index entries_user_idx;")
    psql("create index entries_user_consumed_at_idx on entries (user_id, consumed_at);")
    results.append(measure("(user_id, consumed_at) index, no week window", False))
    results.append(measure("(user_id, consumed_at) index, week window", True))
    psql("analyze entries;")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
