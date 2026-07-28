from pydantic import BaseModel, Field


class QuerySchema(BaseModel):
    query: str = Field(min_length=1, max_length=2_000, description="Natural-language analytics question")
