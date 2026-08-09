import asyncio
import logging

from fastapi import FastAPI, File, HTTPException, UploadFile

from app_data.agentic_loop import run_agent_loop
from app_data.decomposition import planner
from app_data.ingestion import ingest_upload
from app_data.models import Question
from app_data.synthesis import synthesize_answer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


@app.post("/ask")
async def ask(que: Question):
    try:
        research_plan = planner(que.query)  # Returns an object of the class ResearchPlan

        state = await run_agent_loop(research_plan, que.query)

        response = synthesize_answer(state, que)

        return {
            "answer": response.choices[0].message.content,
            "trail": state.research_trail,
            "confidence": state.confidence,
            "sources": list(state.retrieved_chunks),
        }

    except Exception as e:
        logger.exception("Error while processing /ask request")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = await asyncio.to_thread(ingest_upload, file.filename or "", content)
        return {
            "message": "File uploaded and ingested successfully.",
            **result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error while processing /upload request")
        raise HTTPException(status_code=500, detail=str(e))
