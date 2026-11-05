import uuid
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, HTTPException

from app.deps import current_user_id, get_conn
from app.foods import Food, FoodCreate, create_food, list_foods

app = FastAPI(title="Calorie tracker API", version="0.1.0")


@app.get("/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/foods")
def get_foods(
    conn: Annotated[psycopg.Connection, Depends(get_conn)],
    user_id: Annotated[uuid.UUID, Depends(current_user_id)],
) -> list[Food]:
    return list_foods(conn, user_id)


@app.post("/v1/foods", status_code=201)
def post_food(
    data: FoodCreate,
    conn: Annotated[psycopg.Connection, Depends(get_conn)],
    user_id: Annotated[uuid.UUID, Depends(current_user_id)],
) -> Food:
    try:
        return create_food(conn, user_id, data)
    except psycopg.errors.ForeignKeyViolation as exc:
        if exc.diag.constraint_name != "foods_serving_unit_fkey":
            raise
        raise HTTPException(status_code=422, detail="unknown_serving_unit") from exc
