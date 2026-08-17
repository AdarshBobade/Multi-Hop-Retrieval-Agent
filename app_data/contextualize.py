from app_data.models import Conversation
from app_data.config import llm_with_fallback
from app_data.prompts import CONEXTUALIZE_SYSTEM_PROMPT , CONEXTUALIZE_USER_PROMPT
from app_data.logging_config import timer 
from tenacity import (retry, stop_after_attempt, wait_exponential, before_sleep_log)
import logging
logger = logging.getLogger(__name__)



@timer
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def contextualize_query(query:str , history:list[Conversation]):
    if not history:
        return query


    historical_data = "\n\n".join(f"Question:{turn.question}\nAnswer:{turn.answer}" for turn in history)

    prompt = CONEXTUALIZE_USER_PROMPT.format(history=historical_data , query=query)

    logger.info("Retrieving the context from the history of the conversation:")

    response = llm_with_fallback(
        primary_model="openai/gpt-oss-20b",
        fallback_model="openai/gpt-oss-20b",
        max_tokens=350,
        fallback_max_tokens=250,
        messages=[
            {"role": "system", "content": CONEXTUALIZE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    standalone_query = response.choices[0].message.content.strip()
    logger.info(f"Original: '{query}' -> Standalone: '{standalone_query}'")

    return standalone_query
