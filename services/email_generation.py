# 필터링된 행사 목록으로 이메일 생성
from __future__ import annotations
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from services.event_repository import EventRepository
from services.ai_common import build_user_prompt, load_system_prompt, log_llm_response
from models.openai_adapter import OpenAIAdapter
from models.base import BaseLLM
from schemas import EmailGenerationRequest, EmailGenerationResponse

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PROMPT_PATH = BASE_DIR / "prompts" / "email_generation.md"


def load_system_prompt(prompt_path: str | Path = DEFAULT_PROMPT_PATH) -> str:
    path = Path(prompt_path)
    if not path.is_file():
        raise FileNotFoundError(f"시스템 프롬프트를 찾을 수 없습니다: {path}")

    prompt = path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"프롬프트가 비어 있습니다: {path}")

    return prompt


def normalize_events(events: Any) -> list[dict[str, Any]]:
    """DataFrame 형태의 행사 데이터를 LLM이 읽기 좋은 형태로 정규화"""
    if hasattr(events, "to_dict"):
        try:
            events = events.to_dict(orient="records")
        except TypeError:
            raise ValueError("DataFrame을 dict로 변환할 수 없습니다.")

    normalized: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            raise TypeError(f"events[{index}]는 dict 형태여야 합니다")
        normalized.append(dict(event))

    return normalized



def generate_email(llm: BaseLLM, request: EmailGenerationRequest, *, prompt_path: str | Path = DEFAULT_PROMPT_PATH) -> EmailGenerationResponse:
    payload = {
        "events": normalize_events(request.events),
        "language": "Korean",
        "tone": "professional and friendly",
        "recipient_context": request.recipient_name,
        "additional_request": request.additional_request,
    }

    system_prompt = load_system_prompt(prompt_path)
    user_prompt = build_user_prompt(payload, task_description="이메일 초안 생성을 위한 입력 데이터입니다.", xml_tag="email_generation_input")

    response = llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_schema=EmailGenerationResponse
    )

    if not isinstance(response, EmailGenerationResponse):
        raise TypeError("LLM 응답이 EmailGenerationResponse 타입이 아닙니다.")

    log_llm_response("이메일 생성 결과", response)
    return response
