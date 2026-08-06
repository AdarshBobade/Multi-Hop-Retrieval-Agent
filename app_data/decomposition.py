from groq import Groq
from dotenv import load_dotenv
from app_data.config import groq_api
from app_data.prompts import PLANNER_SYSTEM_PROMPT
from app_data.models import ResearchPlan
import json
load_dotenv()

client = Groq(api_key=groq_api)

# Breaking the user query into sub_questions
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
        return {
                    "complexity": "simple",
                    "goal": query,
                    "sub_questions": [
                        {
                            "question": query,
                            "purpose": "Fallback to original query due to planner parsing failure."
                        }
                    ],
                    "planner_status": "fallback"
                }
    


