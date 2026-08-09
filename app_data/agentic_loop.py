import asyncio
from app_data.models import ResearchState
from app_data.retrieval import retrieve , retrieve_async
from app_data.reflection import reflect

async def run_agent_loop(research_plan , original_query):

    # Complexity Routing
    complexity = research_plan.complexity.lower()

    if complexity == "complex":
        initial_queries = [
            task.question
            for task in research_plan.sub_questions
        ]
    else:
        initial_queries = [original_query]



    state = ResearchState(question = original_query,
                                    plan = research_plan,
                                    current_queries = initial_queries,
                                    complexity=complexity,
                                    retrieved_chunks = set(),
                                    visited_queries = set(),
                                    hop_cnt = 0 ,
                                    max_hops = 3,
                                    research_trail = [],
                                    confidence = 0.0,
                                    llm_calls  = 0,
                                    retrieval_calls = 0)


    chunks_before = len(state.retrieved_chunks)

    new_queries = [q for q in state.current_queries if q not in state.visited_queries]
    for q in new_queries:
        state.visited_queries.add(q)

    if new_queries:
        results = await asyncio.gather(*(retrieve_async(q) for q in new_queries))
        for chunk_list in results:
            state.retrieved_chunks.update(chunk_list)
        state.retrieval_calls += len(new_queries)

    chunks_after = len(state.retrieved_chunks)
    new_chunks = chunks_after - chunks_before

    # Checking whether the retrieved data/context is enough to answer (Reflect) :
    # Reflect on Initital evidence
    hop_decision = reflect(state)
    state.llm_calls += 1
    state.confidence = hop_decision.confidence

    # Recording Hop 0 ->
    hop_record = {
        "hop": state.hop_cnt,
        "queries": state.current_queries.copy(),
        "chunks_found": new_chunks,
        "reasoning": hop_decision.reasoning,
        "sufficient": hop_decision.sufficient,
        "next_query": hop_decision.next_query,
        "confidence": hop_decision.confidence
    }

    state.research_trail.append(hop_record)


    # Adaptive Multi-Hop Loop
    while not hop_decision.sufficient and state.hop_cnt < state.max_hops:
        next_query = hop_decision.next_query 

        # Safety check : If no query is generated .
        if next_query is None:
             break
        
        # Safety check : If query already visited
        if next_query in state.visited_queries  :
             break

        state.hop_cnt += 1

        state.visited_queries.add(next_query)
        state.current_queries = [next_query]

        chunks_before = len(state.retrieved_chunks)

        # single query still goes through the async wrapper for consistency
        results = await asyncio.gather(retrieve_async(next_query))
        state.retrieved_chunks.update(results[0])
        state.retrieval_calls += 1

        chunks_after = len(state.retrieved_chunks)

        # Re-evaluate the accumlated evidence
        hop_decision = reflect(state)

        state.llm_calls += 1
        state.confidence = hop_decision.confidence

        new_chunks = chunks_after - chunks_before
        # For Research_trail ->
        hop_record = {
                        "hop": state.hop_cnt,
                        "queries": state.current_queries.copy(),
                        "chunks_found": new_chunks,
                        "reasoning": hop_decision.reasoning,
                        "sufficient": hop_decision.sufficient,
                        "next_query": hop_decision.next_query,
                        "confidence": hop_decision.confidence
                    }

        state.research_trail.append(hop_record)

    return state
        






