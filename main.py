import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from services.event_repository import EventRepository
from services.event_search import get_filter_options_data, filter_and_map_events
from services.email_ai_generation import ai_generate_email
from services.event_ai_search import ai_search_events
from schemas import MailSchedulerCreateRequest, EmailGenerationResponse, EventSearchRequest, EventSearchResponse, AiEventSearchRequest
from models.factory import load_llm
from routers.mail_schedulers import router as mail_scheduler_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경- 프론트엔드 도메인으로 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repository = EventRepository()
app.include_router(mail_scheduler_router)

parse_llm = load_llm(
    provider="claude",
    model="anthropic/claude-haiku-4.5",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

search_llm = load_llm(
    provider="openai",
    model="gpt-5.2",
    api_key=os.getenv("OPENAI_API_KEY")
)

# ==== 검색 =======

@app.get("/api/events/filter-options")
def get_event_filter_options():
    df = repository.load_events_dataframe()
    result = get_filter_options_data(df)
    print(f"[DEBUG] 필터 옵션 값: {result}")

    return result


@app.post("/api/events/search")
def event_keyword_serach(request: EventSearchRequest):
    df = repository.load_events_dataframe()
    events_list = filter_and_map_events(df, request)
    result = {"events": events_list}

    return result


@app.post("/api/events/ai-search")
def event_ai_search(request: AiEventSearchRequest):
    df = repository.load_events_dataframe()
    try:
        result = ai_search_events(parse_llm, search_llm, df, request)
    except Exception as e:
        print(f"[Error] AI 검색 실패 : {e}")
        raise HTTPException(status_code=500, detail=f"AI 검색 중 오류가 발생했습니다: {e}")

    return result

