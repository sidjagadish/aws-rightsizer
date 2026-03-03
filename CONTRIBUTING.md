# Contributing

## Branching

- Work on **feature branches**, not directly on `dev`.
- Use a clear prefix:
  - `feature/short-description` — new work
  - `fix/short-description` — bugfixes

Example:

```bash
git checkout dev
git pull origin dev
git checkout -b feature/add-findings-list
```

## Merging into `dev`

- Open a **pull request (PR)** into `dev` for review.
- Do **not** push directly to `dev` once the team is active; use PRs so everyone stays in sync.

## `main` branch

- **Do not push to `main`.**
- `main` is for release/production; updates to `main` happen via merge from `dev` (or release process), not from feature branches.

## Running the stack locally

1. **Database** — from repo root: `docker compose up -d` (see [README](README.md#database-postgresql-18)).
2. **Backend** — from repo root: `cd server`, `poetry install`, `poetry run uvicorn app.main:app --reload --port 8000 --reload-exclude '.venv'`.
3. **Frontend** — from repo root: `cd client`, `npm install`, `npm run dev`; open http://localhost:5173.

Full step-by-step: [README → Run everything (first time)](README.md#run-everything-first-time).

## Adding dependencies
- Virtual enviornment is managed by `poetry`
- Add new packages using `poetry add <package name>`

## Summary

| Do | Don’t |
|----|--------|
| Branch from `dev`, open PR into `dev` | Push directly to `dev` (after bootstrap) |
| Keep `main` for releases | Push to `main` from feature work |
| Run DB before backend | Skip starting the database |
