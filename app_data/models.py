from pydantic import BaseModel ,Field ,field_validator
from typing import Any , Literal


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
    source: Literal["local", "web", "hybrid"]
    search_depth: Literal["basic", "advanced"] = "basic"

class ResearchPlan(BaseModel):
    complexity : str
    goal : str
    sub_questions : list[ResearchTask]
    retrieval_mode: Literal["local", "web", "hybrid"]

class Evidence(BaseModel):
    content: str
    source_type: Literal["document", "web"]
    source: str
    title: str | None = None
    url: str | None = None
    doc_id: str | None = None
    chunk_id: str | None = None
    citation_id: str | None = None
    chunk_index: int | None = None
    page: int | None = None
    relevance_score: float | None = None
    distance: float | None = None
    published_date: str | None = None
    retrieval_query: str | None = None
    rerank_score: float | None = None


class ResearchState(BaseModel):
    question : str
    plan : ResearchPlan 
    current_queries : list[str] = Field(default_factory=list)
    evidence : list[Evidence] = Field(default_factory=list)
    visited_queries : set[str]
    hop_cnt : int = 0
    max_hops : int = 3
    research_trail : list[dict[str , Any]] = Field(default_factory=list)
    complexity : str
    confidence : float = 0.0
    llm_calls : int = 0
    retrieval_calls : int = 0
    web_search_calls : int = 0
    

class HopDecision(BaseModel):
    sufficient: bool
    reasoning: str
    missing_info : str | None = None
    confidence: float
    next_query: str | None = None
    source: Literal["local", "web", "hybrid"] | None = None

class GroundednessCheck(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    verdict: str  # "fully_supported" | "partially_supported" | "not_supported"
    unsupported_claims: list[str] = []
    reasoning: str



 