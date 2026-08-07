from __future__ import annotations
from pathlib import Path
from typing import Any
import pandas as pd
from models.base import BaseLLM
from schemas import AiEventSearchRequest, EventSearchResponse, AiSearchLLMResponse
from services.ai_common import build_user_prompt, load_system_prompt, log_llm_response
from services.event_fields import KR_TO_EN, SEARCH_FIELDS

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PROMPT_PATH = BASE_DIR / "prompts" / "event_ai_search.md"


def _normalize_df_to_records(df: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    meta_by_id: dict[str, dict[str, Any]] = {}
 
    for _, row in df.iterrows():
        event_id = str(row.get("event_id", ""))
        full: dict[str, Any] = {"event_id": event_id}
 
        for kr_col, en_key in KR_TO_EN.items():
            raw = row.get(kr_col)
            if en_key == "keyword" or en_key == "keywords":
                full["keywords"] = (
                    [v.strip() for v in str(raw).split(",") if v.strip()]
                    if pd.notna(raw)
                    else []
                )
            else:
                full[en_key] = str(raw) if pd.notna(raw) else ""
 
        meta_by_id[event_id] = full
 
    search_records = [
        {k: v for k, v in record.items() if k in SEARCH_FIELDS}
        for record in meta_by_id.values()
    ]
 
    return search_records, meta_by_id



def _assemble_results(matched_ids: list[str], meta_by_id: dict[str, dict[str, Any]]):
    return [meta_by_id[eid] for eid in matched_ids if eid in meta_by_id]


def ai_search_events(
        llm: BaseLLM,
        df: pd.DataFrame,
        request: AiEventSearchRequest,
        *,
        prompt_path: str | Path = DEFAULT_PROMPT_PATH
) -> EventSearchResponse:

    if df.empty:
        return EventSearchResponse(events=[])

    search_records, meta_by_id = _normalize_df_to_records(df)
    payload = {
        "query": request.ai_search,
        "events": search_records
    }
    system_prompt = load_system_prompt(prompt_path)
    user_prompt = build_user_prompt(payload, task_description="사용자 검색 질이와 전체 행사 데이터입니다.", xml_tag = "ai_search_input")

    llm_response = llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_schema=AiSearchLLMResponse
    )
    log_llm_response("AI 검색 LLM 응답", llm_response)
    unique_ids = list(dict.fromkeys(llm_response.matched_event_ids))
    assembled = _assemble_results(unique_ids, meta_by_id)

    return EventSearchResponse(events=assembled)
    