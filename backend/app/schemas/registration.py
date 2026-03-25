from datetime import datetime

from pydantic import BaseModel, Field


class RegistrationCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    form_data: dict = Field(default_factory=dict)
    deadline_at: datetime


class RegistrationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    form_data: dict | None = None


class RegistrationOut(BaseModel):
    id: int
    applicant_id: int
    title: str
    status: str
    deadline_at: datetime
    supplemented_once: bool

    class Config:
        from_attributes = True
