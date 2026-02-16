# AWS Rightsizer

Cloud optimization tool for EC2: analyze utilization and pricing, get cost- and performance-aware rightsizing recommendations.

**Phase 2 bootstrap.** This repo currently provides:

- Project structure baseline
- **PostgreSQL 18** via Docker Compose
- **FastAPI** backend ([server/](server/))
- **React + Vite + Tailwind** frontend ([client/](client/))

---

## Requirements

- **Docker Desktop** – install and have it **running** before starting the database
- **Python 3.11+** (for the backend; on some systems the command is `python3`)
- **Node.js 18+** and npm (for the frontend)

---

## Run everything (first time)

From a fresh clone, use this order. Each section below assumes you’re in the path shown.

1. **Repo root** – start the database:
   ```bash
   docker compose up -d
   docker compose ps   # wait until db shows (healthy)
   ```
2. **Backend** – from repo root:
   ```bash
   cd server
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000 --reload-exclude '.venv'
   ```
   Leave this terminal running; open a new one for the frontend.
3. **Frontend** – from repo root (new terminal):
   ```bash
   cd client
   npm install
   npm run dev
   ```
4. Open **http://localhost:5173** in your browser. The app will talk to the API at http://localhost:8000.

---

## Repo layout

| Path | Description |
|------|-------------|
| `server/` | FastAPI backend. See [Backend (FastAPI)](#backend-fastapi) below. |
| `client/` | React + Vite + TypeScript + Tailwind frontend. [client/README.md](client/README.md) has full details. |
| `docker-compose.yml` | PostgreSQL 18 service (`db`) |

**Contributing** — Branch naming, PRs into `dev`, and how to run the stack: see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Database (PostgreSQL 18)

All database commands below: run from the **repo root** (where `docker-compose.yml` lives).

### Start

```bash
docker compose up -d
```

### Check status

```bash
docker compose ps
```

Wait until the database shows `(healthy)`.

### Verify Postgres

```bash
docker compose exec db psql -U postgres -d rightsizer -c "SELECT version();"
```

You should see PostgreSQL 18.x.

### Stop (keep data)

```bash
docker compose down
```

### Reset (delete data)

Removes all tables and data.

```bash
docker compose down -v
```

### Connection details

| | |
|--|--|
| Host | `localhost` |
| Port | `5432` |
| User | `postgres` |
| Password | `postgres` |
| Database | `rightsizer` |

Connection string (for backend):

```
postgresql+psycopg2://postgres:postgres@localhost:5432/rightsizer
```

---

## Backend (FastAPI)

API runs on **http://localhost:8000**. CORS is enabled for the React dev server (port 5173).

All commands below: run from the **repo root** then `cd server`, or from inside **`server/`**.

### Quick start

```bash
cd server
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000 --reload-exclude '.venv'
```

If your system uses `python3` instead of `python`, use `python3 -m venv .venv` and `python3` for any later commands.

- API root: **http://localhost:8000/**  
- Health: **http://localhost:8000/api/health**  
- DB connectivity check: **http://localhost:8000/api/db/ping** (requires DB running)

### Environment (optional)

Create `server/.env` to override defaults:

| Variable | Default |
|----------|---------|
| `APP_ENV` | `dev` |
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@localhost:5432/rightsizer` |

Ensure the database is running (`docker compose up -d`) before starting the server.

---

## Frontend (React)

All commands below: run from the **repo root** then `cd client`, or from inside **`client/`**.

### Quick start

```bash
cd client
npm install
npm run dev
```

Open **http://localhost:5173**.

### Scripts (from `client/`)

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server (port 5173) |
| `npm run build` | Type-check + production build |
| `npm run lint` | ESLint |
| `npm run preview` | Preview production build |

**Stack:** React 19, React Router 7, Vite 7, TypeScript 5.9, Tailwind CSS 4.

**API:** The app calls the backend at **http://localhost:8000** (override with `VITE_API_BASE_URL`). Planned endpoints: `GET /api/findings`, `GET /api/instances`.

For project structure and more detail, see [client/README.md](client/README.md).

---

## Troubleshooting

- **Database connection refused** – Start the DB first from repo root: `docker compose up -d`, and wait until `docker compose ps` shows `(healthy)`.
- **Port already in use** – Defaults are DB `5432`, API `8000`, frontend `5173`. Stop whatever is using the port or change the app port (e.g. `uvicorn app.main:app --reload --port 8001`).
- **`python: command not found`** – Use `python3` instead of `python` for venv and scripts.
