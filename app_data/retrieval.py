from app_data.ingestion import collection
from app_data.models import Evidence , ResearchTask
from app_data.web_search import web_search
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

async def retrieve_async(query: str , k_closest: int = 5):
    return await asyncio.to_thread(retrieve, query ,k_closest)




async def web_search_async(query: str,search_depth: str = "basic",topic: str = "general") -> list[Evidence]:

    return await asyncio.to_thread(
        web_search,
        query,
        search_depth,
        topic
    )


async def retrieve_for_task(task: ResearchTask) -> list[Evidence]:

    if task.source == "local":
        return await retrieve_async(task.question)

    if task.source == "web":
        return await web_search_async(
            query=task.question,
            search_depth=task.search_depth,
            topic=task.topic
        )

    if task.source == "hybrid":

        local_results, web_results = await asyncio.gather(
            retrieve_async(task.question),
            web_search_async(
                query=task.question,
                search_depth=task.search_depth,
                topic=task.topic
            )
        )

        return local_results + web_results

    return []


def add_to_evidence_pool(evidence_pool: list[Evidence],new_evidence: list[Evidence]) -> int:

    existing = {
        (e.source_type, e.source, e.page, e.content)
        for e in evidence_pool
    }

    added = 0

    for evidence in new_evidence:
        key = (
            evidence.source_type,
            evidence.source,
            evidence.page,
            evidence.content
        )

        if key not in existing:
            evidence_pool.append(evidence)
            existing.add(key)
            added += 1

    return added