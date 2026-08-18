from app_data.ingestion import collection
from app_data.models import Evidence, ResearchTask
from app_data.web_search import web_search
from rank_bm25 import BM25Okapi
from app_data.reranking import rerank
import asyncio
from collections import Counter
import logging
import re

logger = logging.getLogger(__name__)

WEB_QUERY_STOPWORDS = {
    "about", "after", "also", "been", "before", "being", "between",
    "context", "could", "document", "documents", "from", "given", "have",
    "into", "look", "more", "most", "other", "provided", "recent",
    "research", "should", "studies", "study", "than", "that", "their",
    "there", "these", "they", "this", "through", "using", "what", "when",
    "where", "which", "while", "with", "would", "your",
}

bm25_cache = None


def build_bm25_index():
    all_docs = collection.get()
    documents = all_docs["documents"]
    ids = all_docs["ids"]
    metadatas = all_docs["metadatas"]
    tokenized = [doc.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized)
    return bm25, documents, ids, metadatas


def get_bm25_index():
    global bm25_cache
    if bm25_cache is None:
        bm25_cache = build_bm25_index()
    return bm25_cache


def invalidate_bm25_cache():
    global bm25_cache
    bm25_cache = None


def retrieve_bm25(query: str, k_closest: int = 10) -> list[Evidence]:
    bm25, documents, ids, metadatas = get_bm25_index()
    if not documents:
        return []

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    ranked_indices = sorted(
        range(len(scores)), key=lambda i: scores[i], reverse=True
    )[:k_closest]

    evidence = []
    for idx in ranked_indices:
        if scores[idx] <= 0:
            continue
        evidence.append(
            chroma_to_evidence(
                document=documents[idx],
                metadata=metadatas[idx],
                distance=None,
                query=query,
                chunk_id=ids[idx],
            )
        )
    return evidence


def reciprocal_rank_fusion(
    result_lists: list[list[Evidence]], k: int = 60
) -> list[Evidence]:
    scores: dict[str, float] = {}
    items: dict[str, Evidence] = {}

    for result_list in result_lists:
        for rank, evidence in enumerate(result_list):
            key = evidence.chunk_id or evidence.content
            scores[key] = scores.get(key, 0) + 1 / (k + rank + 1)
            items[key] = evidence

    ranked_keys = sorted(scores.keys(), key=lambda key: scores[key], reverse=True)
    return [items[key] for key in ranked_keys]


def retrieve_hybrid_local(
    query: str, retrieval_k: int = 15, final_k: int = 8
) -> list[Evidence]:
    semantic_results = retrieve(query, k_closest=retrieval_k)
    bm25_results = retrieve_bm25(query, k_closest=retrieval_k)
    fused = reciprocal_rank_fusion([semantic_results, bm25_results], k=60)
    reranked = rerank(query, fused[:retrieval_k])
    return reranked[:final_k]


async def retrieve_hybrid_local_async(query: str, k_closest: int = 10):
    return await asyncio.to_thread(retrieve_hybrid_local, query, k_closest)


def retrieve(query: str, k_closest: int = 10) -> list[Evidence]:
    results = collection.query(query_texts=[query], n_results=k_closest)
    evidence = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    for document, metadata, distance, chunk_id in zip(
        documents, metadatas, distances, ids
    ):
        evidence.append(
            chroma_to_evidence(
                document=document,
                metadata=metadata,
                distance=distance,
                query=query,
                chunk_id=chunk_id,
            )
        )

    return evidence


def chroma_to_evidence(
    document: str,
    metadata: dict,
    distance: float | None,
    query: str,
    chunk_id: str | None,
) -> Evidence:
    return Evidence(
        content=document,
        source_type="document",
        source=metadata.get("source", "unknown"),
        title=metadata.get("title"),
        doc_id=metadata.get("doc_id"),
        chunk_id=chunk_id,
        chunk_index=metadata.get("chunk_index"),
        page=metadata.get("page"),
        distance=distance,
        retrieval_query=query,
    )


async def web_search_async(
    query: str, search_depth: str = "basic", topic: str = "general"
) -> list[Evidence]:
    return await asyncio.to_thread(
        web_search,
        query=query,
        search_depth=search_depth,
        topic=topic,
    )


def build_contextual_web_query(query: str, local_evidence: list[Evidence]) -> str:
    """Enrich a vague web request with topic terms found in uploaded PDFs."""
    document_text = " ".join(
        evidence.content[:2000]
        for evidence in local_evidence[:5]
        if evidence.content
    )

    if not document_text:
        return query

    words = re.findall(r"[a-zA-Z][a-zA-Z-]{3,}", document_text.lower())
    term_counts = Counter(
        word
        for word in words
        if word not in WEB_QUERY_STOPWORDS and not word.isdigit()
    )
    topic_terms = [term for term, _ in term_counts.most_common(8)]

    if not topic_terms:
        return query

    enriched_query = (
        f"{query}. Find recent peer-reviewed studies and experimental findings "
        f"about: {' '.join(topic_terms)}"
    )
    logger.info("Context-enriched web query: %s", enriched_query)
    return enriched_query


async def retrieve_for_task(task: ResearchTask) -> list[Evidence]:
    if task.source == "local":
        return await retrieve_hybrid_local_async(task.question)

    if task.source == "web":
        return await web_search_async(
            query=task.question,
            search_depth=task.search_depth,
            topic="general",
        )

    if task.source == "hybrid":
        # Local evidence supplies subject terms for vague web requests.
        local_results = await retrieve_hybrid_local_async(task.question)
        contextual_web_query = build_contextual_web_query(
            task.question,
            local_results,
        )
        web_results = await web_search_async(
            query=contextual_web_query,
            search_depth=task.search_depth,
            topic="general",
        )
        return local_results + web_results

    return []


def add_to_evidence_pool(
    evidence_pool: list[Evidence], new_evidence: list[Evidence]
) -> int:
    existing_keys = {
        (
            evidence.source_type,
            evidence.source,
            evidence.page,
            evidence.chunk_id,
            evidence.content,
        )
        for evidence in evidence_pool
    }

    added = 0
    for evidence in new_evidence:
        key = (
            evidence.source_type,
            evidence.source,
            evidence.page,
            evidence.chunk_id,
            evidence.content,
        )
        if key in existing_keys:
            continue

        evidence.citation_id = f"E{len(evidence_pool) + 1}"
        evidence_pool.append(evidence)
        existing_keys.add(key)
        added += 1

    return added
