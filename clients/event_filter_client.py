import os
import httpx
from typing import Any


async def fetch_events_by_filter(filter_dict: dict) -> list[dict[str, Any]]:
    """POST /events-filter 호출 -> items 목록 반환"""
    base_url = os.getenv("CRAWLER_API_BASE_URL")
    internal_key = os.getenv("INTERNAL_SERVICE_KEY")
    #print(f"[Debug] filter_dict: {filter_dict}")

    payload = {
        "filter": {
            "organizations": filter_dict.get("organizations") or [],
            "event_types": filter_dict.get("event_types") or [],
            "keywords": filter_dict.get("keywords") or [],
            "venue_categories": filter_dict.get("venue_categories") or [],
            **({
                "start_after": filter_dict["start_after"]
            } if filter_dict.get("start_after") else {}),
            **({
                "start_before": filter_dict["start_before"]
            } if filter_dict.get("start_before") else {}),
        },
         
    }

    #print(f"[Debug] payload: {payload}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/events-filter",
            headers={
                "Content-Type": "application/json",
                "X-Internal-Service-Key": internal_key,
            },
            json=payload,
        )

        print(f"[Debug] events-filter 응답 상태: {response.status_code}")
        if response.is_error:
            print(f"[Error] events-filter 응답 상태: {response.status_code}")
            print(f"[Error] events-filter 응답 본문: {response.text}")
            print(f"[Error] events-filter 응답 헤더: {dict(response.headers)}")

        response.raise_for_status()
        data = response.json()

    items = data.get("items") or []

    print(f"[Debug] events-filter 응답 행사 수: {len(items)}")

    return items