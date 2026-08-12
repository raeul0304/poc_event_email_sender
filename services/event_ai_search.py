from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import Any
import io
import pandas as pd
from models.base import BaseLLM
from schemas import AiEventSearchRequest, EventSearchResponse, AiSearchLLMResponse
from services.ai_common import build_user_prompt, load_system_prompt
from services.event_fields import COLUMN_MAP, SEARCH_FIELDS

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PROMPT_PATH = BASE_DIR / "prompts" / "event_ai_search.md"


def _df_to_search_csv(df: pd.DataFrame) -> str:
    """SEARCH_FIELDS에 해당하는 컬럼만 추출해서 CSV 문자열로 변환"""
    kr_to_en = {v: k for k, v in COLUMN_MAP.items() if k in SEARCH_FIELDS}
    available = {kr: en for kr, en in kr_to_en.items() if kr in df.columns}

    search_df = df[list(available.keys())].copy()
    search_df = search_df.rename(columns=available)

    if "event_id" in df.columns:
        search_df.insert(0, "event_id", df["event_id"].values)

    buffer = io.StringIO()
    search_df.to_csv(buffer, index=False)
    return buffer.getvalue()


def _build_meta(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """event_id 기준으로 전체 필드 메타 딕셔너리 생성"""
    meta: dict[str, dict[str, Any]] = {}

    for _, row in df.iterrows():
        event_id = str(row.get("event_id", ""))
        record: dict[str, Any] = {"event_id": event_id}

        for kr_col, en_key in {v: k for k, v in COLUMN_MAP.items()}.items():
            raw = row.get(kr_col)
            if en_key in ("keyword", "keywords"):
                record["keywords"] = (
                    [v.strip() for v in str(raw).split(",") if v.strip()]
                    if pd.notna(raw) else []
                )
            else:
                record[en_key] = str(raw) if pd.notna(raw) else ""

        meta[event_id] = record

    return meta


def _assemble_results(matched_ids: list[str], meta: dict[str, dict[str, Any]]):
    return [meta[eid] for eid in matched_ids if eid in meta]


def ai_search_events(
        llm: BaseLLM,
        df: pd.DataFrame,
        request: AiEventSearchRequest,
        *,
        prompt_path: str | Path = DEFAULT_PROMPT_PATH
) -> EventSearchResponse:

    if df.empty:
        return EventSearchResponse(events=[])

    csv_string = _df_to_search_csv(df)
    meta = _build_meta(df)

    print(f"[AI Search] 총 {len(meta)}개 행사, CSV 길이: {len(csv_string)} chars")

    payload = {
        "current_date": date.today().isoformat(),
        "query": request.ai_search,
        "events": csv_string
    }

    system_prompt = load_system_prompt(prompt_path)
    user_prompt = build_user_prompt(
        payload,
        task_description="사용자 검색 질의와 전체 행사 데이터입니다.",
        xml_tag="ai_search_input"
    )

    llm_response = llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_schema=AiSearchLLMResponse
    )

    unique_ids = list(dict.fromkeys(llm_response.matched_event_ids))
    assembled = _assemble_results(unique_ids, meta)

    return EventSearchResponse(events=assembled)