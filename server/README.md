# AWS Rightsizer – Backend

FastAPI app. Serves the React frontend (CORS allowed for http://localhost:5173).

**Run all commands below from the `server/` directory** (or from repo root: `cd server` first).

For full local setup (database + backend + frontend), see the [repo root README](../README.md).

## Requirements

- Python 3.11+ (use `python3` if `python` is not available)
- PostgreSQL 18 running — from repo root: `docker compose up -d` (see root README)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- **Root:** http://localhost:8000/
- **Health:** http://localhost:8000/api/health

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
│   ├── api/       # Route modules (e.g. health)
│   ├── config.py  # Settings (env)
│   └── main.py    # FastAPI app, CORS, routers
├── requirements.txt
└── README.md
```
