import os
import httpx
from schemas import MailSchedulerCreateRequest, MailSchedulerRunResponse


async def create_mail_scheduler(request: MailSchedulerCreateRequest) -> None:
    base_url = os.getenv("CRAWLER_API_BASE_URL")
    internal_key = os.getenv("INTERNAL_SERVICE_KEY")

    request_body = request.model_dump(
        mode="json",
        exclude_none=True,
    )
    #print(f"[Debug] mail-schedulers 생성 요청: {request_body}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/mail-schedulers",
            headers={
                "Content-Type": "application/json",
                "X-Internal-Service-Key": internal_key,
            },
            json=request_body,
        )

        if response.is_error:
            print(f"[Error] mail-schedulers 응답 본문: {response.text}")

        response.raise_for_status()

    print("[Debug] mail-schedulers 생성 성공")




async def get_mail_schedulers() -> list[dict]:
    base_url = os.getenv("CRAWLER_API_BASE_URL")
    internal_key = os.getenv("INTERNAL_SERVICE_KEY")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{base_url.rstrip('/')}/mail-schedulers",
            headers={"X-Internal-Service-Key": internal_key},
        )

        if response.is_error:
            print(f"[Error] mail-schedulers 조회 응답 본문: {response.text}")

        response.raise_for_status()
        data = response.json()

    items = data.get("items") or []
    print(f"[Debug] 서버에서 받은 mail-schedulers item 수: {len(items)}")
    return items



async def get_single_mail_scheduler(mail_scheduler_id: str) -> dict:
    base_url = os.getenv("CRAWLER_API_BASE_URL")
    internal_key = os.getenv("INTERNAL_SERVICE_KEY")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{base_url.rstrip('/')}/mail-schedulers/{mail_scheduler_id}",
            headers={"X-Internal-Service-Key": internal_key},
        )

        if response.is_error:
            print(f"[Error] mail-scheduler 상세 조회 응답 본문: {response.text}")

        response.raise_for_status()

    data = response.json()
    print(f"[Debug] 서버에서 받은 mail-scheduler 개수: {len(data)}")
    return data




async def update_mail_scheduler(mail_scheduler_id: str, request: MailSchedulerCreateRequest) -> None:
    base_url = os.getenv("CRAWLER_API_BASE_URL")
    internal_key = os.getenv("INTERNAL_SERVICE_KEY")

    request_body = request.model_dump(mode="json", exclude_none=True)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/mail-schedulers/{mail_scheduler_id}/update",
            headers={
                "Content-Type": "application/json",
                "X-Internal-Service-Key": internal_key,
            },
            json=request_body,
        )

        if response.is_error:
            print(f"[Error] mail-schedulers 수정 응답 본문: {response.text}")

        response.raise_for_status()




async def delete_mail_scheduler(mail_scheduler_id: str) -> None:
    base_url = os.getenv("CRAWLER_API_BASE_URL")
    internal_key = os.getenv("INTERNAL_SERVICE_KEY")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/mail-schedulers/{mail_scheduler_id}/delete",
            headers={"X-Internal-Service-Key": internal_key},
        )

        if response.is_error:
            print(f"[Error] mail-schedulers 삭제 응답 본문: {response.text}")

        response.raise_for_status()