from app_data.config import groq_api
from app_data.prompts import SYNTHESIS_SYSTEM_PROMPT , SYNTHESIS_USER_PROMPT , GROUNDEDNESS_SYSTEM_PROMPT ,GROUNDEDNESS_USER_PROMPT
from groq import Groq
from tenacity import (retry, stop_after_attempt, wait_exponential, before_sleep_log)
from app_data.logging_config import timer
from app_data.models import GroundednessCheck
from app_data.evidence_format import format_evidence
import logging
import json

client = Groq(api_key=groq_api)
logger = logging.getLogger(__name__)


@timer
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def check_groundedness(state, original_query, answer_text: str) -> GroundednessCheck:
    logger.info("Groundedness check started.")

    context = format_evidence(state.evidence)

    prompt = GROUNDEDNESS_USER_PROMPT.format(
        question=original_query.query,
        answer=answer_text,
        context=context
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": GROUNDEDNESS_SYSTEM_PROMPT},
                  {"role": "user", "content": prompt}]
    )

    raw_response = response.choices[0].message.content

    print("\n===== PLANNER RAW RESPONSE =====")
    print(repr(raw_response))
    print("================================\n")

    plan_dict = json.loads(raw_response)

    data = json.loads(response.choices[0].message.content)
    check = GroundednessCheck.model_validate(data)

    logger.info(f"Groundedness score: {check.score:.2f}, verdict: {check.verdict}")
    if check.unsupported_claims:
        logger.warning(f"Unsupported claims flagged: {check.unsupported_claims}")

    return check



@timer
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def synthesize_answer(state , original_query):
    logger.info("Synthesis started.")

    context = format_evidence(state.evidence)

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