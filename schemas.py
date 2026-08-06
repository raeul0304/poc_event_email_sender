# 이메일 생성 요청 및 결과 스키마
from typing import Any
from pydantic import BaseModel, Field

class EmailGenerationRequest(BaseModel):
    events: list[dict[str, Any]]
    recipient_name: str | None = None
    additional_request: str | None = None

class EmailGenerationResponse(BaseModel):
    subject: str = Field(description="이메일 제목")
    body: str = Field(description="이메일 본문")