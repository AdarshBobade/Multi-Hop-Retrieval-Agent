from app_data.models import HopDecision , ResearchState
from groq import Groq
from app_data.config import groq_api
from app_data.prompts import REFLECTION_SYSTEM_PROMPT , REFLECTION_USER_PROMPT
from tenacity import (retry, stop_after_attempt, wait_exponential, before_sleep_log)
from app_data.logging_config import timer
import logging
import json

client = Groq(api_key=groq_api)

logger = logging.getLogger(__name__)

#returns JSON for HopDecision
@timer
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def reflect(state : ResearchState) -> HopDecision:
    logger.info("Reflection started.")
    """ 
        Taking current state and asking the LLM whether another retrieval hop is required or not
        
        args:
        state: Current Research State
        
        return:
        returns the Decision

    """
    logger.info(f"Hop {state.hop_cnt}/{state.max_hops}")
    logger.info(f"Current Queries: {state.current_queries}")
    logger.info(f"Visited Queries: {state.visited_queries}")
    logger.info(f"Retrieved {len(state.retrieved_chunks)} chunks.")
            
    try :
        logger.info("Sending reflection request to LLM.")

        context = "\n\n".join(state.retrieved_chunks)
        logger.info(f"Context Size: {len(context.split())} words")

        user_prompt = REFLECTION_USER_PROMPT.format(question=state.question,                                    
                                                    complexity=state.complexity,
                                                    hop=state.hop_cnt,max_hops=state.max_hops,
                                                    visited_queries=state.visited_queries,
                                                    current_queries=state.current_queries,
                                                    num_chunks=len(state.retrieved_chunks),
                                                    context=context
                                                    )

        raw_response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[  {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
                                {"role": "user", "content": user_prompt} ]
                                )

        logger.debug(raw_response.choices[0].message.content)
        decision_data = json.loads(raw_response.choices[0].message.content)
        
        decision = HopDecision.model_validate(decision_data)
        logger.info("Reflection response successfully validated.")

        logger.info(f"Sufficient: {decision.sufficient}")
        logger.info(f"Confidence: {decision.confidence:.2f}")
        logger.info(f"Missing Information: {decision.missing_info}")
        logger.info(f"Next Query: {decision.next_query}")
        logger.info("Reflection completed.")
        return decision

    # If reflection fails completely ->
    except Exception :
        logger.warning("Reflection failed due to an internal error. The research loop was terminated safely to prevent unnecessary retrieval iterations.")
        logger.error("Reflection failed due to parsing/API error. Terminating research to avoid unnecessary retrieval loops.",
                     exc_info=True)
        return HopDecision(
                            sufficient=True,
                            reasoning="Reflection failed. Stopping to avoid infinite loop.",
                            missing_info=None,
                            confidence=0.0,
                            next_query=None
                            )
        


