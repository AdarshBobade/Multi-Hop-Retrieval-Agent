import os
from pathlib import Path

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