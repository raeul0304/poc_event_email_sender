# 키워드 기반 데이터 필터, 데이터프레임 생성, 타입 정리
from typing import Any, Dict, List
import pandas as pd
from schemas import EventSearchRequest
from services.event_fields import (
    COLUMN_MAP,
    COMMA_SEPARATED_FIELDS,
    DROPDOWN_FIELDS,
    FILTER_OPTION_ARRAY_FIELDS,
    FILTER_OPTION_COLUMN_MAP,
)


# ======== 필터 옵션값 ===========
# def get_filter_options_data(df: pd.DataFrame) -> Dict[str, List[str]]:
#     """DataFrame에서 필터 드롭다운을 위한 유니크 값들 추출"""
#     result = {f"{field}s": [] for field in DROPDOWN_FIELDS}
#     if df.empty:
#         return result

#     for field in DROPDOWN_FIELDS:
#         plural_key = f"{field}s"
#         db_column = COLUMN_MAP.get(field)
        
#         if db_column and db_column in df.columns:
#             if field in COMMA_SEPARATED_FIELDS:
#                 values_set = set()
#                 for string_val in df[db_column].dropna():
#                     values_set.update([v.strip() for v in str(string_val).split(",") if v.strip()])
#                 result[plural_key] = sorted(list(values_set))
#             else:
#                 result[plural_key] = sorted(df[db_column].dropna().unique().tolist())
    
#     return result

def get_filter_options_data(
    df: pd.DataFrame,
) -> Dict[str, List[str]]:
    """DataFrame에서 필터 드롭다운용 고유 값을 추출합니다."""
    result = {f"{field}s": [] for field in DROPDOWN_FIELDS}

    if df.empty:
        return result

    for field in DROPDOWN_FIELDS:
        plural_key = f"{field}s"
        db_column = FILTER_OPTION_COLUMN_MAP.get(field)

        if not db_column or db_column not in df.columns:
            continue

        values_set: set[str] = set()

        for raw_value in df[db_column].dropna():
            if field in FILTER_OPTION_ARRAY_FIELDS:
                if isinstance(raw_value, (list, tuple, set)):
                    values_set.update(
                        str(value).strip()
                        for value in raw_value
                        if value is not None
                        and str(value).strip()
                    )
            else: # organizer, event_type, location: 단일 값
                value = str(raw_value).strip()

                if value and value.lower() != "nan":
                    values_set.add(value)

        result[plural_key] = sorted(values_set)

    return result




# ========= 필터 적용 검색 ============
# def _apply_isin_filter(df: pd.DataFrame, column_name: str, values: List[str]) -> pd.DataFrame:
#     """리스트에 정확히 일치하는 값을 필터링"""
#     if values and column_name in df.columns:
#         return df[df[column_name].isin(values)]
#     return df

def _apply_isin_filter(df: pd.DataFrame, column_name: str, values: List[str]) -> pd.DataFrame:
    """단일 DB 값이 요청 목록에 정확히 포함되는 행을 필터링"""
    if not values or column_name not in df.columns:
        return df

    return df[df[column_name].isin(values)]


def _apply_contains_filter(df: pd.DataFrame, column_name: str, search_values: List[str]) -> pd.DataFrame:
    """값 중 하나라도 포함되어 있으면 필터링"""
    if search_values and column_name in df.columns:
        return df[df[column_name].apply(
            lambda x: any(v.lower() in str(x).lower() for v in search_values)
        )]
    return df

def _apply_array_filter(df: pd.DataFrame, column_name: str, search_values: List[str]) -> pd.DataFrame:
    """DB 배열에 요청값이 하나라도 포함된 행을 필터링합니다."""
    if not search_values or column_name not in df.columns:
        return df

    search_set = set(search_values)

    def has_matching_value(raw_value: Any) -> bool:
        if not isinstance(raw_value, (list, tuple, set)):
            return False

        row_values = {
            str(value).strip()
            for value in raw_value
            if value is not None and str(value).strip()
        }

        return bool(search_set.intersection(row_values))

    return df[df[column_name].apply(has_matching_value)]


def _apply_date_filter(df: pd.DataFrame, start_col: str, end_col: str, start_date: str, end_date: str) -> pd.DataFrame:
    """시작 일시와 종료 일시를 기준으로 날짜 범위를 필터링합니다."""
    def _extract_and_parse_dates(series: pd.Series) -> pd.Series:
        extracted_dates = series.astype(str).str.extract(r'(\d{4}-\d{2}-\d{2})')[0]
        return pd.to_datetime(extracted_dates, errors='coerce')

    if start_date and start_col in df.columns:
        df = df[_extract_and_parse_dates(df[start_col]) >= pd.to_datetime(start_date)]
        
    if end_date and end_col in df.columns:
        df = df[_extract_and_parse_dates(df[end_col]) <= pd.to_datetime(end_date)]
        
    return df


def _map_row_to_event(row: pd.Series) -> Dict[str, Any]:
    """API 응답 스펙으로 변환"""
    event_item = {"event_id": str(row.get("event_id", ""))}

    for en_key, kr_key in COLUMN_MAP.items():
        if en_key not in COMMA_SEPARATED_FIELDS:
            val = row.get(kr_key)
            event_item[en_key] = "" if pd.isna(val) else str(val)

    for field in COMMA_SEPARATED_FIELDS:
        plural_key = f"{field}s"
        kr_col = COLUMN_MAP.get(field)
        val = row.get(kr_col)
        if kr_col and pd.notna(val) and str(val).strip() and str(val).lower() != "nan":
            event_item[plural_key] = [v.strip() for v in str(row.get(kr_col, "")).split(",") if v.strip()]
        else:
            event_item[plural_key] = []

    return event_item


# def filter_and_map_events(df: pd.DataFrame, request: EventSearchRequest) -> List[Dict[str, Any]]:
#     if df.empty:
#         return []

#     filtered_df = df.copy()

#     for field in DROPDOWN_FIELDS:
#         plural_key = f"{field}s"
#         req_values = getattr(request, plural_key, [])
#         db_column = COLUMN_MAP.get(field)

#         if req_values and db_column and db_column in filtered_df.columns:
#             if field in COMMA_SEPARATED_FIELDS:
#                 filtered_df = _apply_contains_filter(filtered_df, db_column, req_values)
#             else:
#                 filtered_df = _apply_isin_filter(filtered_df, db_column, req_values)

#     #날짜 필터
#     start_col = COLUMN_MAP.get("start_date")
#     end_col = COLUMN_MAP.get("end_date")
#     if start_col and end_col:
#         filtered_df = _apply_date_filter(filtered_df, start_col, end_col, request.start_date, request.end_date)

#     return [_map_row_to_event(row) for _, row in filtered_df.iterrows()]


def filter_and_map_events(df: pd.DataFrame, request: EventSearchRequest) -> List[Dict[str, Any]]:
    """요청 조건으로 이벤트를 필터링하고 API 응답으로 변환"""
    if df.empty:
        return []

    filtered_df = df.copy()

    for field in DROPDOWN_FIELDS:
        plural_key = f"{field}s"
        request_values = getattr(request, plural_key, []) or []
        db_column = FILTER_OPTION_COLUMN_MAP.get(field)

        if (
            not request_values
            or not db_column
            or db_column not in filtered_df.columns
        ):
            continue

        if field in FILTER_OPTION_ARRAY_FIELDS:
            filtered_df = _apply_array_filter(
                filtered_df,
                db_column,
                request_values,
            )
        else:
            filtered_df = _apply_isin_filter(
                filtered_df,
                db_column,
                request_values,
            )

    # 날짜는 기존 payload.source_row 값 기준
    start_column = COLUMN_MAP.get("start_date")
    end_column = COLUMN_MAP.get("end_date")

    if start_column and end_column:
        filtered_df = _apply_date_filter(
            filtered_df,
            start_column,
            end_column,
            request.start_date,
            request.end_date,
        )

    print(f"\n[DEBUG] 필터링 결과: {len(filtered_df)}")

    return [
        _map_row_to_event(row)
        for _, row in filtered_df.iterrows()
    ]