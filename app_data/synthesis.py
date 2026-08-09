from app_data.config import groq_api
from app_data.prompts import SYNTHESIS_SYSTEM_PROMPT , SYNTHESIS_USER_PROMPT
from groq import Groq
from tenacity import (retry, stop_after_attempt, wait_exponential, before_sleep_log)
from app_data.logging_config import timer
import logging

client = Groq(api_key=groq_api)
logger = logging.getLogger(__name__)

@timer
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def synthesize_answer(state , original_query):
    logger.info("Synthesis started.")

    context = "\n\n".join(state.retrieved_chunks)

    logger.info(f"Synthesizing answer, context size: {len(context.split())} words")

    prompt = SYNTHESIS_USER_PROMPT.format(goal=state.plan.goal , 
                                        context=context ,
                                        query=original_query.query)

    logger.info("Sending prompt to LLM.")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}]
    )
    logger.info("Synthesis completed.")

    return response