from app_data.ingestion import collection
from app_data.models import Evidence
import asyncio

def retrieve(query , k_closest = 5) -> list[Evidence]:
    results = collection.query(query_texts=[query] , n_results=k_closest)
    evidence = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for document, metadata, distance in zip(documents,metadatas,distances):
        evidence.append(
            chroma_to_evidence(
                document=document,
                metadata=metadata,
                distance=distance,
                query=query
            )
        )

    return evidence

def chroma_to_evidence(document: str,metadata: dict,distance: float | None,query: str) -> Evidence:

    return Evidence(
        content=document,
        source_type="document",
        source=metadata.get("source", "unknown"),
        title=metadata.get("title"),
        doc_id=metadata.get("doc_id"),
        page=metadata.get("page"),
        distance=distance,
        retrieval_query=query
    )

async def retrieve_async(query: str):
    return await asyncio.to_thread(retrieve, query)