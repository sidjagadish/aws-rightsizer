# AWS Rightsizer

Cloud optimization tool for EC2: analyze utilization and pricing, get cost- and performance-aware rightsizing recommendations.

**Phase 2 bootstrap.** This repo currently provides:

- Project structure baseline
- **PostgreSQL 18** via Docker Compose
- **React + Vite + Tailwind** frontend (see [client/](client/))

---

## Requirements

- **Docker Desktop** (for the database)
- **Node.js 18+** and npm (for the frontend)

---

## Repo layout

| Path | Description |
|------|-------------|
| `client/` | React + Vite + TypeScript + Tailwind frontend. [client/README.md](client/README.md) has full details. |
| `docker-compose.yml` | PostgreSQL 18 service (`db`) |

---

## Database (PostgreSQL 18)

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

⚠️ Removes all tables and data.

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

## Frontend (React)

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

**API:** The app is configured to call a backend at **http://localhost:8000** (override with `VITE_API_BASE_URL`). Planned endpoints: `GET /api/findings`, `GET /api/instances`. Backend not in this repo yet.

For project structure and more detail, see [client/README.md](client/README.md).
