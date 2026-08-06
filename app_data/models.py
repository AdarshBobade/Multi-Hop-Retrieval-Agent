from pydantic import BaseModel

# Data Validation using Pydantic ->
class Question(BaseModel):
    query :str

class ResearchTask(BaseModel):
    question : str
    purpose :str
    priority : int

class ResearchPlan(BaseModel):
    complexity : str
    goal : str
    sub_questions : list[ResearchTask]

