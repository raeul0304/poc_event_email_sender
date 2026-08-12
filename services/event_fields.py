COLUMN_MAP = {
    "title": "제목",
    "location": "장소",
    "organizer": "주최",
    "start_date": "시작 일시",
    "end_date": "종료 일시",
    "summary": "주제 요약",
    "event_type": "행사 성격",
    "keyword": "주요 키워드",
    "source": "출처",
    "registration_link": "등록 링크",
    "more_info_link": "상세 정보 링크",
    "is_not_free": "유료 여부",
}

KR_TO_EN: dict[str, str] = {v: k for k, v in COLUMN_MAP.items()}

DROPDOWN_FIELDS = ["organizer", "event_type", "location", "keyword"]
COMMA_SEPARATED_FIELDS = ["keyword"]

FILTER_OPTION_COLUMN_MAP = {
    "organizer": "_filter_organization",
    "event_type": "_filter_event_type",
    "location": "_filter_venue_category",
    "keyword": "_filter_keywords",
}
FILTER_OPTION_ARRAY_FIELDS = {
    "keyword",
}

SEARCH_FIELDS: frozenset[str] = frozenset({
    "event_id", "title", "organizer", "event_type",
    "start_date", "end_date", "location", "summary",
    "keyword", "is_not_free",
})