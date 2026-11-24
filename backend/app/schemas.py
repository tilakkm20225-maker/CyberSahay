from pydantic import BaseModel, Field
from typing import Literal

class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=10000)
    channel: Literal["sms", "email", "chat"] = "sms"

class UrlRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)
