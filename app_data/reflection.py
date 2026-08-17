from app_data.models import HopDecision , ResearchState
from groq import Groq
from app_data.config import groq_api
from app_data.prompts import REFLECTION_SYSTEM_PROMPT , REFLECTION_USER_PROMPT
from tenacity import (retry, stop_after_attempt, wait_exponential, before_sleep_log)
from app_data.logging_config import timer
from app_data.evidence_format import format_evidence
import logging
import re
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
    if state.complexity == "simple":
        return HopDecision(
                                sufficient=True,
                                reasoning="Question is categorized as Simple, Reflection layer skipped.",
                                missing_info=None,
                                confidence=0.9,
                                next_query=None,
                                source=None
                                )


    if state.complexity == "complex":
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
        logger.info(f"Retrieved {len(state.evidence)} chunks.")
                
        try :
            logger.info("Sending reflection request to LLM.")
            context = format_evidence(state.evidence)
            
            logger.info(f"Context Size: {len(context.split())} words")

            user_prompt = REFLECTION_USER_PROMPT.format(question=state.question,                                    
                                                        complexity=state.complexity,
                                                        hop=state.hop_cnt,max_hops=state.max_hops,
                                                        visited_queries=state.visited_queries,
                                                        current_queries=state.current_queries,
                                                        num_chunks=len(state.evidence),
                                                        context=context
                                                        )

            response = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[  {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
                                    {"role": "user", "content": user_prompt} ]
                                    )

            logger.debug(response.choices[0].message.content)


            raw_response = response.choices[0].message.content
            if raw_response is None:
                raise ValueError("Reflection response was empty.")

            raw_response = raw_response.strip()

            # Remove code fences like ```json ... ``` or ``` ... ```
            raw_response = re.sub(r"^```(?:json)?\s*", "", raw_response, flags=re.IGNORECASE)
            raw_response = re.sub(r"\s*```$", "", raw_response, flags=re.IGNORECASE)

            # If the model added explanation before or after JSON, extract the first JSON object
            start = raw_response.find("{")
            end = raw_response.rfind("}")

            if start != -1 and end != -1 and end > start:
                raw_response = raw_response[start:end + 1]

            decision_dict = json.loads(raw_response)
            decision = HopDecision.model_validate(decision_dict)
            
            
            logger.info("Reflection response successfully validated.")

            logger.info(f"Sufficient: {decision.sufficient}")
            logger.info(f"Confidence: {decision.confidence:.2f}")
            logger.info(f"Missing Information: {decision.missing_info}")
            logger.info(f"Next Query: {decision.next_query}")
            logger.info("Reflection completed.")
            return decision

        except json.JSONDecodeError:
            logger.exception("Reflection JSON parsing failed.")

            return HopDecision(
                sufficient=True,
                reasoning="Reflection output could not be parsed. Stopping safely.",
                missing_info=None,
                confidence=0.0,
                next_query=None,
                source=None
            )

        except Exception:
            logger.exception("Reflection API call failed.")
            raise
        
    
        


