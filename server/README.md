# AWS Rightsizer – Backend

FastAPI app. Serves the React frontend (CORS allowed for http://localhost:5173).

**Run all commands below from the `server/` directory** (or from repo root: `cd server` first).

For full local setup (database + backend + frontend), see the [repo root README](../README.md).

## Requirements

- Python 3.11+ (use `python3` if `python` is not available)
- PostgreSQL 18 running — from repo root: `docker compose up -d` (see root README)
- Poetry 2.0+ (install from preferred package manager)
## Quick start

```bash
poetry install
poetry run uvicorn app.main:app --reload --port 8000 --reload-exclude '.venv'
```

- **Root:** http://localhost:8000/
- **Health:** http://localhost:8000/api/health
- **DB ping:** http://localhost:8000/api/db/ping (checks backend ↔ Postgres)

## Config

Optional `server/.env`:

| Variable | Default |
|----------|---------|
| `APP_ENV` | `dev` |
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@localhost:5432/rightsizer` |

## Structure

```
server/
├── app/
│   ├── api/       # Route modules (health, db)
│   ├── db/        # SQLAlchemy engine, session, get_db
│   ├── config.py  # Settings (env)
│   └── main.py    # FastAPI app, CORS, routers
├── poetry.lock
├── pyproject.toml
└── README.md
```
