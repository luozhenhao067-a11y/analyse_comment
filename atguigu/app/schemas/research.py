from pydantic import BaseModel, field_validator


class ResearchRequest(BaseModel):
    query:str

    @field_validator("query")
    @staticmethod
    def not_empty(query: str) -> str:
        text = query.strip()

        if not text:
            raise ValueError("输入的研究内容怎么他妈空的")

        return text


class ResearchResponse(BaseModel):
    task_id: str