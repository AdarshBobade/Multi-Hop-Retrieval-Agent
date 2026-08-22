import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app_data.contextualize import contextualize_query
from app_data.agentic_loop import run_agent_loop
from app_data.decomposition import planner
from app_data.ingestion import ingest_upload, list_documents, delete_document, reset_session_database
from app_data.models import Question
from app_data.synthesis import synthesize_answer, check_groundedness


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start every backend session with an empty document index."""
    reset_session_database()
    yield


app = FastAPI(lifespan=lifespan)


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


@app.get("/documents")
def get_documents():
    return {"documents": list_documents()}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.delete("/documents/{doc_id}")
def remove_document(doc_id: str):
    deleted_count = delete_document(doc_id)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": "Document deleted.", "chunks_removed": deleted_count}


@app.post("/ask")
async def ask(que: Question):
    try:
        standalone_query = contextualize_query(query=que.query, history=que.history)
        research_plan = planner(standalone_query)

        state = await run_agent_loop(
            research_plan,
            standalone_query,
            web_search=que.web_search,
            deep_research=que.deep_research,
        )

        response = synthesize_answer(state, standalone_query)
        answer_text = response.choices[0].message.content

        groundedness = check_groundedness(state, standalone_query, answer_text)

        citations = [
            {
                "id": evidence.citation_id,
                "source_type": evidence.source_type,
                "source": evidence.source,
                "title": evidence.title,
                "url": evidence.url,
                "page": evidence.page,
                "doc_id": evidence.doc_id,
                "chunk_id": evidence.chunk_id,
                "published_date": evidence.published_date,
                "content": evidence.content,
            }
            for evidence in state.evidence
        ]

        return {
            "answer": answer_text,
            "trail": state.research_trail,
            "confidence": state.confidence,
            "citations": citations,
            "groundedness": groundedness.model_dump(),
            "retrieval_calls": state.retrieval_calls,
            "web_search_calls": state.web_search_calls,
            "llm_calls": state.llm_calls,
            "document_evidence_count": sum(
                evidence.source_type == "document" for evidence in state.evidence
            ),
            "web_evidence_count": sum(
                evidence.source_type == "web" for evidence in state.evidence
            ),
            "research_mode": {
                "web_search": que.web_search,
                "deep_research": que.deep_research,
            },
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
