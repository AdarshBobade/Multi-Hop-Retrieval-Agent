from fastapi import FastAPI ,HTTPException
from app_data.decomposition import planner
from app_data.models import Question 
from app_data.agentic_loop import run_agent_loop
from app_data.synthesis import synthesize_answer
import asyncio
import logging

app = FastAPI()

logger = logging.getLogger(__name__)

@app.post("/ask")
async def ask(que : Question):

    try:
        
        research_plan = planner(que.query) # Returns an object of the class ResearchPlan 

        state = await run_agent_loop(research_plan, que.query)
       
        response = synthesize_answer(state , que)

        return {"answer": response.choices[0].message.content, 
                "trail" : state.research_trail ,
                "confidence": state.confidence, 
                "sources": list(state.retrieved_chunks)}

    
    except Exception as e:

        logger.exception("Error while processing /ask request")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
