from fastapi import FastAPI ,HTTPException
from app_data.decomposition import planner
from app_data.config import groq_api
from app_data.models import Question 
from app_data.agentic_loop import run_agent_loop
from app_data.prompts import SYNTHESIS_SYSTEM_PROMPT , SYNTHESIS_USER_PROMPT
from groq import Groq
import logging

app = FastAPI()
client = Groq(api_key=groq_api)

logger = logging.getLogger(__name__)

@app.post("/ask")
def ask(que : Question):

    try:
        
        research_plan = planner(que.query) # Returns an object of the class ResearchPlan 

        state = run_agent_loop(research_plan, que.query)
       
        context = "\n\n".join(state.retrieved_chunks)
        prompt = SYNTHESIS_USER_PROMPT.format(goal=research_plan.goal , 
                                            context=context ,
                                            query=que.query)

        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}]
        )
        return {"answer": response.choices[0].message.content, "trail" : state.research_trail ,"sources": list(state.retrieved_chunks) }

    
    except Exception as e:

        logger.exception("Error while processing /ask request")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
