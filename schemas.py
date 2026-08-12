# 이메일 생성 요청 및 결과 스키마
from typing import Any, List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

Weekday = Literal[
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
]


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


#===== 스케줄러 - 이메일 전송 =======
class SchedulerFilter(BaseModel):
    organizations: List[str] = []
    event_types: List[str] = []
    keywords: List[str] = []
    venue_categories: List[str] = []
    start_after: Optional[datetime] = None
    start_before: Optional[datetime] = None


class ScheduleItem(BaseModel):
    mail_scheduler_id: UUID
    filter: SchedulerFilter
    mail_address_list: List[str]


class MailSchedulerRunRequest(BaseModel):
    schedules: List[ScheduleItem]

class MailSchedulerRunResponse(BaseModel):
    status: str


class MailSchedulerTestResponse(BaseModel):
    recipients: List[str]
    subject: str
    matched_event_count: int
    sent_at: str
    error: Optional[str] = None


# ===== 스케줄 CRUD ======
class MailSchedulerCreateRequest(BaseModel):
    filter: SchedulerFilter
    time_term: Optional[int] = 365
    frequent_weekday: List[Weekday] = []
    frequent_hour: Optional[int] = None
    mail_address_list: List[EmailStr]


class MailSchedulerResponse(BaseModel):
    mail_scheduler_id: str
    filter: SchedulerFilter
    time_term: int
    frequent_weekday: List[Weekday]
    frequent_hour: int
    mail_address_list: List[str]
    created_at: datetime
    updated_at: datetime