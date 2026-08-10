import os
import httpx
from typing import Any

CRAWLER_API_BASE_URL = os.getenv("CRAWLER_API_BASE_URL")
CRAWLER_API_KEY = os.getenv("INTERNAL_SERVICE_KEY")

async def fetch_events_by_filter(filter_dict: dict) -> list[dict[str, Any]]:
    """POST /events-filter 호출 -> items 목록 반환"""
    payload = {
        "filter": {
            "organizations": filter_dict.get("organizations", []),
            "event_types": filter_dict.get("event_types", []),
            "keywords": filter_dict.get("keywords", []),
            "venue_categories": filter_dict.get("venue_categories", []),
        }
    }

    if filter_dict.get("start_after"):
        payload["filter"]["start_after"] = filter_dict["start_after"]
    if filter_dict.get("start_before"):
        payload["filter"]["start_before"] = filter_dict["start_before"]

    print(f"[Debug] events-filter 요청 payload: {payload}")

    async with httpx.AsyncClient() as client:
        response  = await client.post(
            f"{CRAWLER_API_BASE_URL}/events-filter",
            headers={
                "Content-Type": "application/json",
                "X-Internal-Service-Key": CRAWLER_API_KEY,
            },
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

    items = data.get("items", [])
    print(f"[Debug] events-filter 응답 행사 수: {len(items)}")
    return items