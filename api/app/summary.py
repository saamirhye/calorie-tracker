import datetime
import uuid

import psycopg
from psycopg.rows import class_row
from pydantic import BaseModel


class DaySummary(BaseModel):
    date: datetime.date
    entries: int
    calories: float
    protein: float
    carbs: float
    fat: float


def get_day_summary(conn: psycopg.Connection, user_id: uuid.UUID, day: datetime.date) -> DaySummary:
    with conn.cursor(row_factory=class_row(DaySummary)) as cur:
        cur.execute(
            """
            SELECT %(day)s::date AS date,
                    count(*) AS entries,
                    coalesce(round(sum(calories * servings), 1), 0) AS calories,
                    coalesce(round(sum(protein * servings), 1), 0) AS protein,
                    coalesce(round(sum(carbs * servings), 1), 0) AS carbs,
                    coalesce(round(sum(fat * servings), 1), 0) AS fat
            FROM entries
            WHERE user_id = %(user_id)s AND deleted_at IS NULL
              AND (consumed_at AT TIME ZONE timezone)::date = %(day)s
            """,
            {"day": day, "user_id": user_id},
        )
        summary = cur.fetchone()
        assert summary is not None
        return summary
