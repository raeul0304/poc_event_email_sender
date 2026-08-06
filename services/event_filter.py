# 키워드 기반 데이터 필터, 데이터프레임 생성, 타입 정리
from __future__ import annotations
from collections.abc import Sequence, Iterable
from typing import Any
import pandas as pd


COLUMN_MAP={
    "제목": "title",
    "장소": "location",
    "주최": "organizer",
    "시작 일시": "start_date",
    "종료 일시": "end_date",
    "주제 요약": "summary",
    "행사 성격": "event_type",
    "주요 키워드": "keywords",
    "출처": "source",
    "등록 링크": "registration_link",
    "상세 정보 링크": "more_info_link",
    "유료 여부": "is_free",
}

EXCLUDE_COLUMNS = {"Index", "링크", "종료 일시", "유료 여부", "첨부파일 유무"}













# 키워드 기반 필터
def filter_events_by_keywords(events: pd.DataFrame, keywords: str | Sequence[str]) -> pd.DataFrame:
    """입력한 키워드 중 하나 이상이 포함된 행사만 반환"""

    if isinstance(keywords, str):
        keywords = keywords.split(",")  #우선 리스트로 받는다고 가정...

    searchable_text =(
        events[events.columns.difference(EXCLUDE_COLUMNS)].fillna("").astype(str).agg(" ".join, axis=1).str.casefold()
    )

    matched = searchable_text.apply(
        lambda text: any(
            keyword in text
            for keyword in keywords
        )
    )

    filtered_events = events.loc[matched].copy()
    print(f"키워드 기반 필터링 결과: {len(filtered_events)}개의 행사가 선택됨\n {filtered_events.shape[0]}")

    return filtered_events