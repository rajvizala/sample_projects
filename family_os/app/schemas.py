from typing import List

from pydantic import BaseModel, Field


class UpdateCreate(BaseModel):
    person_id: int
    category: str = Field(min_length=2, max_length=50)
    text: str = Field(min_length=4, max_length=500)
    mood: str = Field(min_length=2, max_length=30)


class MemoryCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    detail: str = Field(min_length=5, max_length=500)
    people: List[str]
    importance: int = Field(default=2, ge=1, le=5)
