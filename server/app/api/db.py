"""DB connectivity check endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.db import get_db
import app.models
from app.db import Base

router = APIRouter(tags=["db"])



def check_lists(table_list_a,table_list_b):
    tables_not_in_search_list  = []
    for table in table_list_a:
        if table not in table_list_b:
           tables_not_in_search_list.append(table) 
    return tables_not_in_search_list




@router.get("/db/ping")
def db_ping(db: Session = Depends(get_db)):# this could be far faster and cleaner 
    try:

        """Run a trivial query to verify backend ↔ database connectivity."""
        schema = Base.metadata.tables
        db.execute(text("SELECT 1"))
        db_tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'; ")).scalars().all()

        tables_not_in_schema = check_lists(schema.keys(),db_tables) # check if the table exists but is not in the schema, will fail/error if a table can be reached but its not in the schema
        if len(tables_not_in_schema) != 0:
            printable_list = ', '.join(tables_not_in_schema) 
            error_message = "error the following tables are reachable but not in the schema "+printable_list
            return {"status": error_message, "database": "connected", }
        
        tables_not_in_db = check_lists(db_tables,schema.keys())# check if the tables in the schema also exists in the db
        IGNORED_TABLES = {"alembic_version"}
        tables_not_in_db = [t for t in tables_not_in_db if t not in IGNORED_TABLES]

        if len(tables_not_in_db) != 0:
            printable_list = ', '.join(tables_not_in_db) 
            error_message = "error the following tables are in the schema but not in the db "+printable_list
            return {"status":error_message, "database": "connected" }

        return {"status": "ok", "database": "connected","db_tables":db_tables}
    except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "database": str(e)}
            )



