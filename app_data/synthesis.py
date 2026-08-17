import logging
import json
import re

from app_data.config import llm_with_fallback
from app_data.prompts import (
    SYNTHESIS_SYSTEM_PROMPT,
    SYNTHESIS_USER_PROMPT,
    GROUNDEDNESS_SYSTEM_PROMPT,
    GROUNDEDNESS_USER_PROMPT,
)
from tenacity import (retry, stop_after_attempt, wait_exponential, before_sleep_log)
from app_data.logging_config import timer
from app_data.models import GroundednessCheck
from app_data.evidence_format import format_evidence

logger = logging.getLogger(__name__)


def _groundedness_fallback(reason: str) -> GroundednessCheck:
    logger.warning("Groundedness fallback triggered: %s", reason)
    return GroundednessCheck(
        score=0.0,
        verdict="not_supported",
        unsupported_claims=["Malformed model output"],
        reasoning=f"{reason} A conservative fallback was applied to avoid a backend error.",
    )


def _parse_groundedness_response(raw_response: str | None) -> GroundednessCheck:
    if raw_response is None:
        return _groundedness_fallback("No groundedness response was returned.")

    cleaned = (raw_response or "").strip()
    if not cleaned:
        return _groundedness_fallback("Groundedness response was empty.")

    # Remove markdown fences like ```json ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.IGNORECASE)

    # If model added extra text around JSON, grab the first object
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return _groundedness_fallback(f"Malformed groundedness JSON: {exc.msg}.")

    if not isinstance(data, dict):
        return _groundedness_fallback("Groundedness response is not a JSON object.")

    try:
        return GroundednessCheck.model_validate(data)
    except Exception as exc:
        logger.warning("Groundedness validation failed: %s", exc)
        return _groundedness_fallback(
            f"Model output did not match the expected schema: {exc}."
        )


@timer
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def check_groundedness(state, question:str, answer_text: str) -> GroundednessCheck:
    logger.info("Groundedness check started.")

    context = format_evidence(
        state.evidence,
        max_items=10,
        max_chars_per_item=1200,
        max_total_chars=10000,
    )

    prompt = GROUNDEDNESS_USER_PROMPT.format(
        question=question,
        answer=answer_text,
        context=context
    )

    response = llm_with_fallback(
        primary_model="openai/gpt-oss-20b",
        fallback_model="openai/gpt-oss-20b",
        max_tokens=500,
        fallback_max_tokens=350,
        messages=[
            {"role": "system", "content": GROUNDEDNESS_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    raw_response = response.choices[0].message.content

    check = _parse_groundedness_response(raw_response)

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
def synthesize_answer(state , query:str):
    logger.info("Synthesis started.")

    context = format_evidence(
        state.evidence,
        max_items=10,
        max_chars_per_item=1400,
        max_total_chars=12000,
    )

    logger.info(f"Synthesizing answer, context size: {len(context.split())} words")

    prompt = SYNTHESIS_USER_PROMPT.format(goal=state.plan.goal , 
                                        context=context ,
                                        query=query,
                                        complexity=state.complexity)

    logger.info("Sending prompt to LLM.")
    response = llm_with_fallback(
                                    messages=[
                                        {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                                        {"role": "user", "content": prompt}
                                    ],
                                    primary_model="openai/gpt-oss-120b",
                                    fallback_model="openai/gpt-oss-20b",
                                    reasoning_effort="medium",
                                    max_tokens=1800,
                                    fallback_max_tokens=1200,
                                )
    logger.info("Synthesis completed.")

    return response
