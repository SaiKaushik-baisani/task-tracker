"""Pydantic models used to validate task requests and responses."""

from pydantic import BaseModel, Field, field_validator


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)

    @field_validator("title")
    @classmethod
    def fields_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be blank.")
        return value


class TaskUpdate(TaskCreate):
    done: bool


class TaskRead(BaseModel):
    id: int
    title: str
    done: bool
