from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import db, health
from app.api.runs import router as runs_router
from app.api.instance import insta_router
from app.api.metrics import metrics_router
from app.api.recommendations import recommendations_router
from app.api.findings import findings_router
import app.models



app = FastAPI(title="AWS Rightsizer API")

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(db.router, prefix="/api")
app.include_router(runs_router, prefix="/api")
app.include_router(insta_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(findings_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "AWS Rightsizer API"}