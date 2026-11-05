import datetime
import uuid
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import psycopg
from psycopg.rows import class_row
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class Entry(BaseModel):
    id: uuid.UUID
    food_id: uuid.UUID
    food_name: str
    serving_unit: str
    serving_size: float
    calories: int
    protein: float
    carbs: float
    fat: float
    servings: float
    consumed_at: datetime.datetime
    timezone: str


class EntryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    food_id: uuid.UUID
    servings: Decimal = Field(gt=0, max_digits=6, decimal_places=2)
    consumed_at: AwareDatetime
    timezone: str

    @field_validator("timezone")
    @classmethod
    def must_be_known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("unknown timezone") from exc
        return value


def create_entry(conn: psycopg.Connection, user_id: uuid.UUID, data: EntryCreate) -> Entry | None:
    with conn.cursor(row_factory=class_row(Entry)) as cur:
        cur.execute(
            """
            INSERT INTO entries (user_id, food_id, food_name, serving_unit, serving_size,
                  calories, protein, carbs, fat, servings, consumed_at, timezone)
            SELECT %(user_id)s, id, name, serving_unit, serving_size,
                  calories, protein, carbs, fat, %(servings)s, %(consumed_at)s, %(timezone)s
            FROM foods
            WHERE id = %(food_id)s AND deleted_at IS NULL
                  AND (visibility = 'public' OR created_by_user_id = %(user_id)s)
            RETURNING id, food_id, food_name, serving_unit, serving_size, calories,
                  protein, carbs, fat, servings, consumed_at, timezone
            """,
            {**data.model_dump(), "user_id": user_id},
        )
        return cur.fetchone()
