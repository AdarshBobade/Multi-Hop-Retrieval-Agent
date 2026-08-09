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


if __name__ == "__main__":
    print(ingest_pdf("data/notes.pdf"))
    print("Ingested !")
