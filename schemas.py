# 이메일 생성 요청 및 결과 스키마
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass
from uuid import UUID

@dataclass
class EmailResult:
    success: bool
    message: str
    raw: Any = None

class EmailGenerationRequest(BaseModel):
    events: list[dict[str, Any]]
    recipient_name: str | None = None
    additional_request: str | None = None

class EmailGenerationResponse(BaseModel):
    subject: str = Field(description="이메일 제목")
    body: str = Field(description="이메일 본문")

class EventSearchRequest(BaseModel):
    organizers: List[str] = []
    event_types: List[str] = []
    keywords: List[str] = []
    locations: List[str] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class EventItem(BaseModel):
    event_id: str
    title: str
    location: str
    organizer: str
    start_date: str
    end_date: str
    summary: str
    event_type: str
    keywords: List[str]
    source: str
    registration_link: str
    more_info_link: str
    is_not_free: str

class EventSearchResponse(BaseModel):
    events: List[EventItem]


class AiEventSearchRequest(BaseModel):
    ai_search: str = Field(description="자연어 검색 쿼리")

class AiSearchLLMResponse(BaseModel):
    matched_event_ids: List[str] = Field(description="쿼리에 매칭된 행사의 event_id 목록")


#===== 스케줄러 =======
class SchedulerFilter(BaseModel):
    organizations: List[str] = []
    event_types: List[str] = []
    keywords: List[str] = []
    venue_categories: List[str] = []
    start_after: Optional[str] = None
    start_before: Optional[str] = None


class ScheduleItem(BaseModel):
    mail_scheduler_id: UUID
    filter: SchedulerFilter
    mail_address_list: List[str]


class MailSchedulerRunRequest(BaseModel):
    schedules: List[ScheduleItem]

class MailSchedulerRunResponse(BaseModel):
    status: str
