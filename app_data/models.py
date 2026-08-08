from pydantic import BaseModel ,Field ,field_validator

# Data Validation using Pydantic ->
class Question(BaseModel):
    query :str = Field(min_length=1 , max_length=300)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Query cannot be empty.")

        return value

class ResearchTask(BaseModel):
    question : str
    purpose :str
    priority : int

class ResearchPlan(BaseModel):
    complexity : str
    goal : str
    sub_questions : list[ResearchTask]

class ResearchState(BaseModel):
    question : str
    goal : str
    current_queries : list[str]
    retrieved_chunks : set[str]
    visited_queries : set[str]
    hop_cnt : int = 0
    max_hops : int
    research_trail : list[str]
    complexity : str
    confidence : float = 0.0
    is_finished : bool

class HopDecision(BaseModel):
    sufficient: bool
    reasoning: str
    missing_info : str | None
    confidence: float
    next_query: str | None

