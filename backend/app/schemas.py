
from pydantic import BaseModel, Field, field_validator
from typing import Literal


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=10000)

    channel: Literal["sms", "email", "chat"] = "sms"

    input_mode: Literal[
        "single_message",
        "conversation"
    ] = "single_message"

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot contain only whitespace")
        return value


class UrlRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)
