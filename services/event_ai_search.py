from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import Any
import io
import pandas as pd
from models.base import BaseLLM
from schemas import AiEventSearchRequest, EventSearchResponse, AiSearchLLMResponse, QueryParseResult
from services.ai_common import build_user_prompt, load_system_prompt
from services.event_fields import COLUMN_MAP, SEARCH_FIELDS
from services.event_search import _apply_date_filter, _apply_contains_filter, _map_row_to_event

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PROMPT_PATH = BASE_DIR / "prompts" / "event_ai_search.md"
QUERY_PARSER_PROMPT_PATH = BASE_DIR / "prompts" / "query_parser.md"


# ===================== 쿼리 파싱 =====================

def _parse_query(llm: BaseLLM, query: str) -> QueryParseResult:
    payload = {
        "current_date": date.today().isoformat(),
        "query": query
    }
    system_prompt = load_system_prompt(QUERY_PARSER_PROMPT_PATH)
    user_prompt = build_user_prompt(
        payload,
        task_description="사용자 검색 질의입니다.",
        xml_tag="query_input"
    )
    result = llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_schema=QueryParseResult
    )
    print(f"[QueryParser] {result.model_dump()}")
    return result


# ===================== Python 필터 =====================

def _apply_python_filters(df: pd.DataFrame, parsed: QueryParseResult) -> pd.DataFrame:
    filtered = df.copy()

    # 날짜 필터 — 기존 함수 재활용
    start_col = COLUMN_MAP.get("start_date")
    end_col = COLUMN_MAP.get("end_date")
    if start_col and end_col:
        filtered = _apply_date_filter(
            filtered, start_col, end_col,
            parsed.start_date or "",
            parsed.end_date or ""
        )

    # 장소 텍스트 매칭 — 기존 함수 재활용
    if parsed.location:
        loc_col = COLUMN_MAP.get("location")
        if loc_col:
            filtered = _apply_contains_filter(filtered, loc_col, [parsed.location])

    # venue_category 필터
    if parsed.venue_categories:
        vc_col = "_filter_venue_category"
        if vc_col in filtered.columns:
            filtered = _apply_contains_filter(filtered, vc_col, parsed.venue_categories)

    # 주최 필터 — 기존 함수 재활용
    if parsed.organizers:
        org_col = "_filter_organization"
        if org_col in filtered.columns:
            filtered = _apply_contains_filter(filtered, org_col, parsed.organizers)

    # 키워드 필터
    if parsed.keywords:
        kw_col = "_filter_keywords"
        if kw_col in filtered.columns:
            def has_keyword(val: Any) -> bool:
                if not isinstance(val, (list, tuple, set)):
                    return False
                row_kws = {str(v).strip().lower() for v in val if v}
                return any(k.lower() in row_kws for k in parsed.keywords)
            filtered = filtered[filtered[kw_col].apply(has_keyword)]

    # 행사 유형 필터
    if parsed.event_types:
        et_col = "_filter_event_type"
        if et_col in filtered.columns:
            filtered = _apply_contains_filter(filtered, et_col, parsed.event_types)

    # 유료 여부 필터
    if parsed.is_not_free is not None:
        fee_col = COLUMN_MAP.get("is_not_free")
        if fee_col and fee_col in filtered.columns:
            free_indicators = {"아니오", "무료", "n", "없음"}
            paid_indicators = {"예", "유료", "y", "있음"}
            target = paid_indicators if parsed.is_not_free else free_indicators
            filtered = filtered[
                filtered[fee_col].astype(str).str.strip().str.lower().isin(target)
            ]

    print(f"[PythonFilter] {len(df)}개 → {len(filtered)}개")
    return filtered


# ===================== CSV 변환 =====================

def _df_to_search_csv(df: pd.DataFrame) -> str:
    kr_to_en = {v: k for k, v in COLUMN_MAP.items() if k in SEARCH_FIELDS}
    available = {kr: en for kr, en in kr_to_en.items() if kr in df.columns}

    search_df = df[list(available.keys())].copy()
    search_df = search_df.rename(columns=available)

    if "event_id" in df.columns:
        search_df.insert(0, "event_id", df["event_id"].values)

    buffer = io.StringIO()
    search_df.to_csv(buffer, index=False)
    return buffer.getvalue()


# ===================== 메타 빌드 =====================

def _build_meta(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    kr_to_en = {v: k for k, v in COLUMN_MAP.items()}
    meta: dict[str, dict[str, Any]] = {}

    for _, row in df.iterrows():
        event_id = str(row.get("event_id", ""))
        record: dict[str, Any] = {"event_id": event_id}

        for kr_col, en_key in kr_to_en.items():
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


# ===================== 메인 함수 =====================

def ai_search_events(
        parse_llm: BaseLLM,
        search_llm: BaseLLM,
        df: pd.DataFrame,
        request: AiEventSearchRequest,
        *,
        prompt_path: str | Path = DEFAULT_PROMPT_PATH
) -> EventSearchResponse:

    if df.empty:
        return EventSearchResponse(events=[])

    meta = _build_meta(df)

    # 1단계: 쿼리 파싱 (Haiku)
    parsed = _parse_query(parse_llm, request.ai_search)

    # 2단계: Python 필터
    filtered_df = _apply_python_filters(df, parsed)

    if filtered_df.empty:
        print("[AI Search] Python 필터 결과 없음 → 빈 결과 반환")
        return EventSearchResponse(events=[])

    # 3단계: semantic_query 유무로 분기
    if parsed.semantic_query:
        csv_string = _df_to_search_csv(filtered_df)
        payload = {
            "current_date": date.today().isoformat(),
            "query": parsed.semantic_query,
            "events": csv_string
        }
        system_prompt = load_system_prompt(prompt_path)
        user_prompt = build_user_prompt(
            payload,
            task_description="사용자 검색 질의와 필터링된 행사 데이터입니다.",
            xml_tag="ai_search_input"
        )
        llm_response = search_llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=AiSearchLLMResponse
        )
        unique_ids = list(dict.fromkeys(llm_response.matched_event_ids))
        print(f"[AI Search] semantic 매칭 결과: {len(unique_ids)}건")
        return EventSearchResponse(events=_assemble_results(unique_ids, meta))

    else:
        # Python 필터 결과 그대로 반환
        assembled = [
            _map_row_to_event(row)
            for _, row in filtered_df.iterrows()
        ]
        print(f"[AI Search] Python 필터만으로 결과: {len(assembled)}건")
        return EventSearchResponse(events=assembled)