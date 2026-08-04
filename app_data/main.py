from fastapi import FastAPI
from pydantic import BaseModel
from app_data.retrieval import retrieve
from app_data.config import groq_api
from groq import Groq

app = FastAPI()
client = Groq(api_key=groq_api)


class Question(BaseModel):
    query :str


@app.post("/ask")
def ask(q : Question):
    chunks = retrieve(q.query)
    context = "\n\n".join(chunks)
    prompt = f"Answer using only this context:\n{context}\n\nQuestion: {q.query}"
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"answer": response.choices[0].message.content, "sources": chunks}
