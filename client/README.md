# AWS Rightsizer – Frontend

React + Vite + TypeScript + Tailwind CSS. Phase 2 scaffold: routing and UI shell in place.

**Run all commands below from the `client/` directory** (or from repo root: `cd client` first).

For full local setup (database + backend + frontend), see the [repo root README](../README.md).

## Requirements

- Node.js 18+ and npm

## Quick start

```bash
npm install
npm run dev
```

Open **http://localhost:5173** in your browser. The app expects the backend at http://localhost:8000 (see root README to run the API).

## Scripts

| Command       | Description                    |
|--------------|--------------------------------|
| `npm run dev`    | Start dev server (port 5173)   |
| `npm run build`  | Type-check + production build  |
| `npm run lint`   | Run ESLint                     |
| `npm run preview`| Preview production build       |

## Project structure

```
client/
├── public/           # Static assets (e.g. favicon)
├── src/
│   ├── api/          # API helpers (e.g. http.ts → backend base URL)
│   ├── app/          # Routing (routes.tsx)
│   ├── pages/        # Route components (Welcome, Findings, Optimization)
│   ├── index.css     # Global styles (Tailwind)
│   └── main.tsx      # Entry: RouterProvider + root
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Stack

- **React 19** + **React Router 7**
- **Vite 7**
- **TypeScript 5.9**
- **Tailwind CSS 4**

## Backend / API

The app calls the FastAPI backend at **http://localhost:8000** (override with `VITE_API_BASE_URL`).  
Backend lives in [server/](../server/) at the repo root. Run it with `uvicorn app.main:app --reload --port 8000 --reload-exclude '.venv'` from `server/` (see root [README](../README.md)).  
Current endpoint: `GET /api/health`. Planned: `GET /api/findings`, `GET /api/instances`.
