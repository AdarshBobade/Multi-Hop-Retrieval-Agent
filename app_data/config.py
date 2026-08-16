import os
from pathlib import Path
import logging

from dotenv import find_dotenv, load_dotenv

# Load .env file from app_data or project root directory
env_app_data = Path(__file__).resolve().parent / ".env"
env_root = Path(__file__).resolve().parent.parent / ".env"

if env_app_data.exists():
    load_dotenv(env_app_data)
elif env_root.exists():
    load_dotenv(env_root)
else:
    load_dotenv(find_dotenv(usecwd=True))

groq_api = os.getenv("GROQ_API_KEY")
hf_token = os.getenv("HF_TOKEN")
tavily_api = os.getenv("TAVILY_API_KEY")

logger = logging.getLogger(__name__)

from groq import Groq, RateLimitError


client = Groq(api_key=groq_api)


def llm_with_fallback(
                        messages,
                        primary_model,
                        fallback_model=None,
                        reasoning_effort=None,
                        max_tokens=3000
                    ):
    try:
        kwargs = {
            "model": primary_model,
            "messages": messages,
            "max_tokens": max_tokens
        }

        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort

        return client.chat.completions.create(**kwargs)

    except RateLimitError:
        if fallback_model is None:
            raise

        logger.warning(
            f"{primary_model} hit rate limit. "
            f"Switching to {fallback_model}."
        )

        return client.chat.completions.create(
            model=fallback_model,
            messages=messages
        )