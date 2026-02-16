# AWS Rightsizer – Frontend

React + Vite + TypeScript + Tailwind CSS. Phase 2 scaffold: routing and UI shell in place.

## Quick start

```bash
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

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

The app expects an API at **http://localhost:8000** (override with `VITE_API_BASE_URL`).  
Planned endpoints: `GET /api/findings`, `GET /api/instances`. Backend is not part of this repo yet.
