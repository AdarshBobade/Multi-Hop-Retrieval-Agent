from sentence_transformers import CrossEncoder
from app_data.models import Evidence

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L2-v2")

def rerank(query, evidence: list[Evidence] , top_k = 5) -> list[Evidence]:

    if not evidence:
        return []

    pairs = [[query, item.content] for item in evidence ]

    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(evidence, scores),
        key=lambda x: x[1],
        reverse=True
    )

    for item, score in ranked:
        item.rerank_score = float(score)

    
    return [
        item
        for item, _ in ranked[:top_k]
    ]


