import asyncio
from app_data.models import ResearchState , ResearchTask
from app_data.retrieval import retrieve_for_task, add_to_evidence_pool
from app_data.reflection import reflect


def count_calls(task_source: str) -> tuple[int, int]:
    """Returns (retrieval_calls, web_search_calls) for a given task source."""
    if task_source == "local":
        return 1, 0
    if task_source == "web":
        return 0, 1
    if task_source == "hybrid":
        return 1, 1
    return 0, 0

async def run_agent_loop(research_plan , original_query):

    # Complexity Routing
    complexity = research_plan.complexity.lower()

    if complexity == "complex":
        initial_tasks = research_plan.sub_questions
    else:
        initial_tasks = [
            ResearchTask(
                question=original_query,
                purpose="Answer the user's question",
                priority=1,
                source=research_plan.retrieval_mode,
                search_depth="basic"
                
            )
        ]



    state = ResearchState(question = original_query,
                                    plan = research_plan,
                                    current_queries = [task.question for task in initial_tasks],
                                    complexity=complexity,
                                    visited_queries = set(),
                                    hop_cnt = 0 ,
                                    max_hops = 3,
                                    research_trail = [],
                                    confidence = 0.0,
                                    llm_calls  = 0,
                                    retrieval_calls = 0)



    tasks_to_run = [task for task in initial_tasks if task.question not in state.visited_queries]

    for task in tasks_to_run:
        state.visited_queries.add(task.question)

    if tasks_to_run:

        results = await asyncio.gather(
            *[
                retrieve_for_task(task)
                for task in tasks_to_run
            ]
        )

        retrieved_evidence = [evidence for result in results for evidence in result]

        new_evidence = add_to_evidence_pool(
            state.evidence,
            retrieved_evidence
        )

        for task in tasks_to_run:
            r_calls, w_calls = count_calls(task.source)
            state.retrieval_calls += r_calls
            state.web_search_calls += w_calls

    else:
        retrieved_evidence = []
        new_evidence = 0

    

    # Checking whether the retrieved data/context is enough to answer (Reflect) :
    # Reflect on Initital evidence
    hop_decision = reflect(state)

    state.llm_calls += 1
    state.confidence = hop_decision.confidence

    # Recording Hop 0 ->
    hop_record = {
        "hop": state.hop_cnt,
        "queries": state.current_queries.copy(),
        "source": [task.source for task in tasks_to_run],
        "evidence_found": len(retrieved_evidence) if tasks_to_run else 0,
        "new_evidence": new_evidence,
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

        # No retrieval source specified
        if not hop_decision.source:
            break

        state.hop_cnt += 1

        state.visited_queries.add(next_query)
        state.current_queries = [next_query]


        next_task = ResearchTask(question=next_query,
                                purpose=(hop_decision.missing_info or "Retrieve additional evidence"),
                                priority=1,
                                source=hop_decision.source,
                                search_depth="basic"
                                
                            )
        

        # single query still goes through the async wrapper for consistency
        results = await retrieve_for_task(next_task)

        r_calls, w_calls = count_calls(next_task.source)
        state.retrieval_calls += r_calls
        state.web_search_calls += w_calls

        new_evidence = add_to_evidence_pool(state.evidence,results)



        # Re-evaluate the accumlated evidence
        hop_decision = reflect(state)

        state.llm_calls += 1
        state.confidence = hop_decision.confidence

        # For Research_trail ->
        hop_record = {
                        "hop": state.hop_cnt,
                        "queries": [next_query],
                        "source": next_task.source,
                        "evidence_found": len(results),
                        "new_evidence": new_evidence,
                        "reasoning": hop_decision.reasoning,
                        "missing_info": hop_decision.missing_info,
                        "sufficient": hop_decision.sufficient,
                        "next_query": hop_decision.next_query,
                        "confidence": hop_decision.confidence
                    }

        state.research_trail.append(hop_record)

        if new_evidence == 0:
            break

    return state
        






