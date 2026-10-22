# Weekly report: index results

Measured on 22 Oct 2026.

## What was measured

The remaining-calories report in `db/queries.sql`: seven days for one user, with daily calories eaten against the target. It was run for `perf_user_1`, week starting 12 Oct 2026.

## Setup

- Database: `tracker_perf` in the local Docker Postgres 16.15. Not the dev database.
- Data: 52,730 entries (990 soft deleted), 21 users, 13 MB. Built by `generate_entries.sql`.
- The report returns the same rows in every version (output checksum `c339a188`).

## Method

Each version ran six times with `explain (analyze, buffers)`. The first run is dropped and the table shows the median of the other five. `measure_week_report.py` repeats the whole measurement and prints the raw numbers. It drops and creates indexes, so run it only on `tracker_perf`.

## Results

| Version | Median (ms) | Runs (ms) | Scan on `entries` | Rows read | Buffers |
|---|---|---|---|---|---|
| No index, no week window | 9.862 | 9.695, 9.862, 10.003, 9.838, 9.871 | Seq Scan | 51,740 | 1,340 hit |
| `user_id` index, no week window | 2.851 | 2.833, 3.016, 3.175, 2.756, 2.851 | Bitmap Heap Scan | 2,595 | 706 hit, 5 read |
| `(user_id, consumed_at)` index, no week window | 2.821 | 2.809, 2.796, 2.927, 2.821, 3.082 | Bitmap Heap Scan | 2,595 | 706 hit, 16 read |
| `(user_id, consumed_at)` index, week window | 0.406 | 0.453, 0.446, 0.406, 0.384, 0.391 | Bitmap Heap Scan | 37 | 19 hit |

## What it shows

- An index on `user_id` stops Postgres reading every user's rows. The report is about 3.5 times faster (9.9 ms to 2.9 ms).
- Changing the index to `(user_id, consumed_at)` alone makes no difference (2.85 ms and 2.82 ms). The query still asks for the user's whole history, 660 days, to show seven.
- Adding the week window to the query is what lets the second column help. It reads 37 rows instead of 2,595, and runs about 7 times faster than the `user_id` index and about 24 times faster than no index (0.41 ms against 9.9 ms).
- The window compares the raw `consumed_at` column. An earlier attempt filtered on the calculated local date, which cannot use the index. It still read all 2,636 of the user's rows and only saved the grouping work.

## Limits

- One machine, one user, one week, warm cache. The very first run of a plan is much slower (an early single run of the unindexed report took 36 ms) and is not counted here.
- 5 runs per version. Differences under about half a millisecond are noise.
- Not yet measured at 10 times the data. A sequential scan should grow with the table, and the indexed version should stay close to flat.
