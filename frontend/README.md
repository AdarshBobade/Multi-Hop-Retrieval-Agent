# MultiHop frontend

React + Vite + TypeScript UI for the Multi-Hop Retrieval Agent.

## Develop

From the repo root, start the API:

```bash
uvicorn app_data.main:app --reload
```

Then in this directory:

```bash
npm install
npm run dev
```

The Vite dev server proxies `POST /ask` to `http://127.0.0.1:8000`.
