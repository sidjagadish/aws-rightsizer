from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import db, health

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


@app.get("/")
def root():
    return {"message": "AWS Rightsizer API"}