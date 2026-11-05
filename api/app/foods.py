import uuid
from decimal import Decimal

import psycopg
from psycopg.rows import class_row
from pydantic import BaseModel, ConfigDict, Field


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


class FoodCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    description: str | None = None
    serving_unit: str
    serving_size: Decimal = Field(gt=0, max_digits=6, decimal_places=2)
    calories: int = Field(ge=0, le=2_147_483_647)
    protein: Decimal = Field(ge=0, max_digits=6, decimal_places=1)
    carbs: Decimal = Field(ge=0, max_digits=6, decimal_places=1)
    fat: Decimal = Field(ge=0, max_digits=6, decimal_places=1)
    barcode: str | None = Field(default=None, max_length=255)


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


def create_food(conn: psycopg.Connection, user_id: uuid.UUID, data: FoodCreate) -> Food:
    with conn.cursor(row_factory=class_row(Food)) as cur:
        cur.execute(
            """
            INSERT INTO foods (name, description, serving_unit, serving_size,
                    calories, protein, carbs, fat, barcode, visibility, created_by_user_id)
            VALUES (%(name)s, %(description)s, %(serving_unit)s, %(serving_size)s, %(calories)s,
                    %(protein)s, %(carbs)s, %(fat)s, %(barcode)s, 'private', %(user_id)s)
            RETURNING id, name, description, serving_unit, serving_size,
                    calories, protein, carbs, fat, barcode
            """,
            {**data.model_dump(), "user_id": user_id},
        )
        food = cur.fetchone()
        assert food is not None
        return food
