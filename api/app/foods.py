import uuid

import psycopg
from psycopg.rows import class_row
from pydantic import BaseModel


class Food(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    serving_unit: str
    serving_size: float
    calories: int
    protein: float
    carbs: float
    fat: float
    barcode: str | None


def list_foods(conn: psycopg.Connection, user_id: uuid.UUID) -> list[Food]:
    with conn.cursor(row_factory=class_row(Food)) as cur:
        cur.execute(
            """
            SELECT id, name, description, serving_unit, serving_size,
                    calories, protein, carbs, fat, barcode
            FROM foods
            WHERE deleted_at IS NULL AND (visibility = 'public' OR created_by_user_id = %s)
            ORDER BY name, id
            """,
            (user_id,),
        )
        return cur.fetchall()
