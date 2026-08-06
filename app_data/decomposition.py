from groq import Groq
from dotenv import load_dotenv
from app_data.config import groq_api
from app_data.prompts import PLANNER_SYSTEM_PROMPT
from app_data.models import ResearchPlan, ResearchTask
from tenacity import (retry, stop_after_attempt, wait_exponential, before_sleep_log)
import logging
import json
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

client = Groq(api_key=groq_api)

# Breaking the user query into sub_questions

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def planner(query:str):

 
    response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                        {"role": "user" , "content" : query}]
                    )

    # LLM Returns a string containing JSON :
    # SO first Parsing JSON :
    
    
    try :
        plan_dict = json.loads(response.choices[0].message.content)
        research_plan = ResearchPlan.model_validate(plan_dict) # Validating LLM Response
        return research_plan
    
    except json.JSONDecodeError :
        return ResearchPlan(
                        complexity="simple",
                        goal=query,
                        sub_questions=[
                            ResearchTask(
                                question=query,
                                purpose="Fallback due to planner parsing failure.",
                                priority=0
                            )
                        ]
                    )
    


