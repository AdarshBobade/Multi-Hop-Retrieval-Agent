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

