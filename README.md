# Multi-Hop-Retrieval-Agent

A multi-hop research agent that decomposes complex questions, iteratively retrieves and verifies evidence, and synthesizes cited answers from real sources.

## Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install groq
uvicorn app_data.main:app --reload --port 8000
```

API:
- `POST /ask` with `{ "query": "..." }`
- `POST /upload` with multipart form field `file` (PDF)
## Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5176 and proxies `/ask` and `/upload` to the FastAPI server on port 8000.
