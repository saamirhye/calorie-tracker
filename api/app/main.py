import uuid
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI

from app.deps import current_user_id, get_conn
from app.foods import Food, list_foods

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
