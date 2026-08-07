import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from services.event_repository import EventRepository
from services.event_filter import get_filter_options_data, filter_and_map_events
from services.email_generation import generate_email
from schemas import EmailGenerationRequest, EmailGenerationResponse, EventSearchRequest, EventSearchResponse
from models.factory import load_llm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경- 프론트엔드 도메인으로 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repository = EventRepository()


@app.post("/api/events/filter-options")
def get_event_filter_options():
    df = repository.load_events_dataframe()
    result = get_filter_options_data(df)

    return result



@app.post("/api/events/search")
def get_event_filter_options(request: EventSearchRequest):
    df = repository.load_events_dataframe()
    events_list = filter_and_map_events(df, request)

    return {"events": events_list}