import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from services.event_repository import EventRepository
from services.event_filter import filter_events_by_keywords
from services.email_generation import generate_email
from schemas import EmailGenerationRequest, EmailGenerationResponse
from models.factory import load_llm

app = FastAPI()


@app.post("/api/events/filter-options")
def get_event_filter_options():

    return



@app.post("/api/events/search")
def get_event_filter_options():

    return