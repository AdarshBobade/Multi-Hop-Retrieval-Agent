from fastapi import FastAPI
from pydantic import BaseModel
from app_data.retrieval import retrieve
from app_data.decomposition import planner
from app_data.config import groq_api
from groq import Groq

app = FastAPI()
client = Groq(api_key=groq_api)

# Data Validation using Pydantic ->
class Question(BaseModel):
    query :str


@app.post("/ask")
def ask(que : Question):
    retrieved_chunks = set() #Deduplicate chunks retrieved from multiple sub-questions.
    
    research_plan = planner(que.query) # Returns a JSON of Complexity ,Subquestions , priority

    for q in research_plan["sub_questions"]:
        for chunk in retrieve(q["question"]):
            retrieved_chunks.add(chunk)

    context = "\n\n".join(retrieved_chunks)
    prompt = f"Answer using only this context:\n{context}\n\nQuestion: {que.query}"
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"answer": response.choices[0].message.content, "sources": retrieved_chunks}
