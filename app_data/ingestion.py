import uuid
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from pypdf import PdfReader

client = chromadb.PersistentClient(path="./chroma_db")
embed_fn = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection("docs", embedding_function=embed_fn)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


def chunk_text(text, chunk_size=75):
    words = text.split()
    overlap = 50  # Overlapping Chunking
    return [
        " ".join(words[i : i + chunk_size])
        for i in range(0, len(words), chunk_size - overlap)
    ]


def ingest_pdf(path: str | Path) -> dict:
    path = Path(path)
    reader = PdfReader(str(path))
    full_text = " ".join(page.extract_text() or "" for page in reader.pages)

    if not full_text.strip():
        raise ValueError("No extractable text found in the PDF.")

    chunks = chunk_text(full_text)
    if not chunks:
        raise ValueError("PDF produced no text chunks.")

    doc_id = uuid.uuid4().hex
    collection.add(
        documents=chunks,
        ids=[f"{doc_id}-{i}" for i in range(len(chunks))],
        metadatas=[{"source": path.name, "doc_id": doc_id} for _ in chunks],
    )

    return {
        "doc_id": doc_id,
        "filename": path.name,
        "chunks": len(chunks),
        "pages": len(reader.pages),
    }


def save_upload(filename: str, content: bytes) -> Path:
    if not filename:
        raise ValueError("Filename is required.")

    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Only PDF files are supported.")

    if not content:
        raise ValueError("Uploaded file is empty.")

    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError(f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")

    safe_stem = Path(filename).stem.replace(" ", "_")[:80] or "document"
    dest = UPLOAD_DIR / f"{safe_stem}_{uuid.uuid4().hex[:8]}{suffix}"
    dest.write_bytes(content)
    return dest


def ingest_upload(filename: str, content: bytes) -> dict:
    path = save_upload(filename, content)
    result = ingest_pdf(path)
    result["path"] = str(path)
    return result


if __name__ == "__main__":
    print(ingest_pdf("data/notes.pdf"))
    print("Ingested !")
