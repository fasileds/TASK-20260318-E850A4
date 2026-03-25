from pydantic import BaseModel, Field


class ReviewActionRequest(BaseModel):
    action: str
    comments: str | None = Field(default=None, max_length=2000)


class BatchReviewRequest(BaseModel):
    registration_ids: list[int] = Field(min_length=1, max_length=50)
    action: str
    comments: str | None = Field(default=None, max_length=2000)
