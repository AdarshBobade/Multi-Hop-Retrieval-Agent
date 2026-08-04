import chromadb
from pypdf import PdfReader
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

client = chromadb.PersistentClient(path="./chroma_db")
embed_fn = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
                )

collection = client.get_or_create_collection('docs' , embedding_function=embed_fn)

def chunk_text(text , chunk_size = 500):
    words = text.split()
    overlap = 50    # Overlapping Chunking 
    return [" ".join(words[i:i + chunk_size]) for i in range(0 , len(words) ,chunk_size - overlap)]

def ingest_pdf(path):
    reader = PdfReader(path)
    full_text = " ".join(page.extract_text() or "" for page in reader.pages)
    chunks = chunk_text(full_text)
    collection.add(
        documents=chunks,
        ids =[f"{path}-{i}" for i in range(len(chunks))]
        )

if __name__ == "__main__":
    ingest_pdf("data/notes.pdf")
    print("Ingested !")

