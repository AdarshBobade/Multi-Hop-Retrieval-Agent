from app_data.config import llm_with_fallback
from app_data.prompts import PLANNER_SYSTEM_PROMPT , PLANNER_USER_PROMPT
from app_data.models import ResearchPlan, ResearchTask
from tenacity import (retry, stop_after_attempt, wait_exponential, before_sleep_log)
import logging
from app_data.logging_config import timer
import json


logger = logging.getLogger(__name__)


# Breaking the user query into sub_questions

@timer
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def planner(query:str) -> ResearchPlan:

    #logging the function INFO
    logger.info("Planner started.")
    logger.info(f"Question: {query}")

    logger.info(f"Query Length: {len(query.split())} words")

    user_prompt = PLANNER_USER_PROMPT.format(query=query)
    response = llm_with_fallback(
                    primary_model="openai/gpt-oss-20b",
                    fallback_model="qwen/qwen3.6-27b",
                    max_tokens=800,
                    fallback_max_tokens=600,
                    messages=[
                        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                        {"role": "user" , "content" : user_prompt}]
                    )

    # LLM Returns a string containing JSON :
    # SO first converting to JSON :
    try :

        raw_response = response.choices[0].message.content.strip()

        if raw_response.startswith("```"):
            raw_response = raw_response.removeprefix("```json")
            raw_response = raw_response.removesuffix("```").strip()

        plan_dict = json.loads(raw_response)

        research_plan = ResearchPlan.model_validate(plan_dict)# Validating LLM Response
        
        

        logger.info(f"Planner classified query as '{research_plan.complexity}'.")
        logger.info(f"Research Goal: {research_plan.goal}")
        logger.info(f"Generated {len(research_plan.sub_questions)} sub-questions.")

        logger.info("Planner completed successfully.")
        return research_plan
        

    except json.JSONDecodeError :
        logger.error("Planner response parsing failed.",exc_info=True)
        return ResearchPlan(
                        complexity="simple",
                        goal=query,
                        retrieval_mode="local",
                        sub_questions=[
                            ResearchTask(
                                question=query,
                                purpose="Fallback due to planner parsing failure.",
                                priority=1,
                                source="local",
                                search_depth="basic"
                                
                            )
                        ]
                    )
    


