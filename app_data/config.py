import os
from dotenv import load_dotenv

load_dotenv()
groq_api = os.getenv('GROQ_API_KEY')
hf_token = os.getenv("HF_TOKEN")