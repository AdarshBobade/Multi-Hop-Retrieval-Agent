from fastapi import FastAPI
from pydantic import BaseModel
from app_data.retrieval import retrieve
from app_data.decomposition import planner
from app_data.config import groq_api
from app_data.models import Question 
from app_data.prompts import SYNTHESIS_SYSTEM_PROMPT , SYNTHESIS_USER_PROMPT
from groq import Groq

app = FastAPI()
client = Groq(api_key=groq_api)


@app.post("/ask")
def ask(que : Question):
    retrieved_chunks = set() #Deduplicate chunks retrieved from multiple sub-questions.
    
    research_plan = planner(que.query) # Returns an object of the class ResearchPlan 

    complexity = research_plan.complexity
    if complexity == "complex":
        questions = [task.question for task in research_plan.sub_questions]

    elif complexity == "simple":
        questions = [que.query]

    for question in questions:
        for chunk in retrieve(question):
            retrieved_chunks.add(chunk)

    context = "\n\n".join(retrieved_chunks)
    prompt = SYNTHESIS_USER_PROMPT.format(goal=research_plan.goal , 
                                          context=context ,
                                          query=que.query)

    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                  {"role": "user", "content": prompt}]
    )
    return {"answer": response.choices[0].message.content, "sources": retrieved_chunks}
