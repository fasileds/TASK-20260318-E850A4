from pydantic import BaseModel, Field


class MaterialChecklistCreate(BaseModel):
    item_key: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=200)
    required: bool = True


class SupplementRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)
