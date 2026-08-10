import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from services.event_repository import EventRepository
from services.event_search import get_filter_options_data, filter_and_map_events
from services.email_generation import generate_email
from services.event_ai_search import ai_search_events
from schemas import EmailGenerationRequest, EmailGenerationResponse, EventSearchRequest, EventSearchResponse, AiEventSearchRequest
from models.factory import load_llm
from routers.mail_schedulers import router as mail_scheduler_router

load_dotenv()
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
print("\n========== AFTER INCLUDE ==========")

for route in app.routes:
    print(
        type(route).__name__,
        getattr(route, "path", None),
        getattr(route, "methods", None),
    )

print("===================================")


@app.post("/api/mail-schedulers/run-test")
async def run_test():
    print("[TEST] 요청 들어옴")
    return {"status": "ok"}

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
    llm = load_llm(provider="openai", model="gpt-5.2", api_key=os.getenv("OPEN_API_KEY"))

    try:
        result = ai_search_events(llm, df, request)
    except Exception as e:
        print(f"[Error] AI 검색 실패 : {e}")
        raise HTTPException(status_code=500, detail=f"AI 검색 중 오류가 발생했습니다: {e}")

    return result



# ====== 스케줄 등록, 조회, 수정 =======





# ====== 스케줄러 실행 - 이메일 발송 =====
