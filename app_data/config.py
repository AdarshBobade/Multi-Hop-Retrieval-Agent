import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
groq_api = os.getenv('GROQ_API_KEY')
hf_token = os.getenv("HF_TOKEN")