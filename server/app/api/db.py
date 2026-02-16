"""DB connectivity check endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(tags=["db"])


@router.get("/db/ping")
def db_ping(db: Session = Depends(get_db)):
    """Run a trivial query to verify backend ↔ database connectivity."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
