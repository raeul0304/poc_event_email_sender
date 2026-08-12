import os
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Header, HTTPException, Depends, status, Response, Request
from schemas import MailSchedulerRunRequest, MailSchedulerRunResponse, MailSchedulerCreateRequest, MailSchedulerResponse, MailSchedulerTestResponse
from clients.event_filter_client import fetch_events_by_filter
from clients.mail_scheduler_crud_client import create_mail_scheduler, get_mail_schedulers, update_mail_scheduler, delete_mail_scheduler, get_single_mail_scheduler
from services.email_html_renderer import render_email_html
from services.email_sender import send_email

router = APIRouter(prefix="/api/mail-schedulers")

KST = timezone(timedelta(hours=9))


def verify_internal_key(x_internal_service_key: str = Header(...)):
    """scheduler sent X-internal-Service-Key 검증"""
    expected = os.getenv("INTERNAL_SERVICE_KEY")
    if x_internal_service_key != expected:
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")



async def process_schedule(schedule) -> str:
    """스케줄별 처리"""
    scheduler_id = schedule.mail_scheduler_id
    try: 
        filter_dict = schedule.filter.model_dump(mode="json", exclude_none=True,)

        events = await fetch_events_by_filter(filter_dict)
        if not events:
            print(f"[Debug] {schedule.mail_scheduler_id} → 매칭 행사 없음 (skipped)")
            return "skipped"

        recipients = [address.strip() for address in schedule.mail_address_list if address and address.strip()]
        if not recipients:
            print(f"[Error] {scheduler_id} → 수신 이메일 주소 없음")
            return "failed"

        subject = f"[행사 알림] 관심 조건에 맞는 행사 {len(events)}건"
        text_body = (
            f"관심 조건에 맞는 행사 {len(events)}건이 확인되었습니다.\n"
            "자세한 내용은 HTML 형식의 이메일에서 확인해 주세요."
        )
        html_body = render_email_html(items=events,user_name="사용자",)

        email_result = await send_email(
            to=recipients,
            subject=subject,
            body=text_body,
            html_body=html_body,
        )

        if not email_result.success:
            print(f"[Error] {scheduler_id} → 이메일 발송 실패: {email_result.message}")
            return "failed"

        print(f"[Debug] {scheduler_id} → {len(events)}건 매칭, 이메일 발송 완료")
        return "sent"


    except Exception as exc:
        print(
            f"[Error] {scheduler_id} 처리 실패: "
            f"{type(exc).__name__}: {exc}"
        )
        return "failed"



@router.post("/run", response_model=MailSchedulerRunResponse)
async def run_mail_scheduler(request: MailSchedulerRunRequest, _: None = Depends(verify_internal_key)):
    print(f"[Debug] 수신된 스케줄 수: {len(request.schedules)}")
    if not request.schedules:
            return MailSchedulerRunResponse(status="ok")

    results = await asyncio.gather(
        *[process_schedule(schedule) for schedule in request.schedules]
    )
    print(f"[Debug] 처리 결과: {results}")

    if all(result == "sent" for result in results):
        result_status  = "ok"
    elif all(result == "failed" for result in results):
        result_status  = "failed"
    else:
        result_status  = "skipped"

    return MailSchedulerRunResponse(status=result_status)


# 메일 발송 테스트
@router.post("/test", response_model=MailSchedulerTestResponse)
async def test_mail_scheduler(request: MailSchedulerCreateRequest):
    filter_dict = request.filter.model_dump(mode="json", exclude_none=True)
    now = datetime.now(KST)
    time_term = request.time_term or 365
    filter_dict["start_after"] = now.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    filter_dict["start_before"] = (now + timedelta(days=time_term)).strftime("%Y-%m-%dT%H:%M:%S+09:00")

    events = await fetch_events_by_filter(filter_dict)
    recipients = [a.strip() for a in request.mail_address_list if a and a.strip()]
    subject = f"[테스트] 관심 조건에 맞는 행사 {len(events)}건"

    if not events:
        return MailSchedulerTestResponse(
            recipients=recipients,
            subject=subject,
            matched_event_count=0,
            sent_at=now.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
            error="매칭된 행사가 없습니다.",
        )

    if not recipients:
        return MailSchedulerTestResponse(
            recipients=[],
            subject=subject,
            matched_event_count=len(events),
            sent_at=now.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
            error="수신 이메일 주소가 없습니다.",
        )

    text_body = f"관심 조건에 맞는 행사 {len(events)}건이 확인되었습니다."
    html_body = render_email_html(items=events, user_name="사용자")
    result = await send_email(to=recipients, subject=subject, body=text_body, html_body=html_body)

    return MailSchedulerTestResponse(
        recipients=recipients,
        subject=subject,
        matched_event_count=len(events),
        sent_at=now.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        error=None if result.success else result.message,
    )




# CRUD
@router.post("", status_code=status.HTTP_201_CREATED, response_class=Response)
async def create_mail_scheduler_api(request: MailSchedulerCreateRequest) -> Response:
    await create_mail_scheduler(request)
    return Response(status_code=status.HTTP_201_CREATED)



@router.get("")
async def get_mail_schedulers_api():
    items = await get_mail_schedulers()
    response_body = {"items": items}
    #print(f"[Debug] front로 전달하는 mail-schedulers: {response_body}")
    return response_body


@router.get("/{mail_scheduler_id}")
async def get_single_mail_scheduler_api(mail_scheduler_id: str):
    data = await get_single_mail_scheduler(mail_scheduler_id)
    #print(f"[Debug] front로 전달하는 mail-scheduler: {data}")
    return data



@router.post("/{mail_scheduler_id}/update", status_code=status.HTTP_200_OK, response_class=Response)
async def update_mail_scheduler_api(mail_scheduler_id: str, request: MailSchedulerCreateRequest) -> Response:
    print(f"\n[DEBUG] 스케줄 업데이트 {mail_scheduler_id}")
    await update_mail_scheduler(mail_scheduler_id, request)
    return Response(status_code=status.HTTP_200_OK)


@router.post("/{mail_scheduler_id}/delete", status_code=status.HTTP_200_OK, response_class=Response)
async def delete_mail_scheduler_api(mail_scheduler_id: str) -> Response:
    print(f"\n[DEBUG] 스케줄 삭제 {mail_scheduler_id}")
    await delete_mail_scheduler(mail_scheduler_id)
    return Response(status_code=status.HTTP_200_OK)








print(">>>>>> mail_schedulers 라우터 로드됨")
print(
    f">>>>>>>>>> mail_schedulers 등록 라우트: "
    f"{[(r.path, r.methods) for r in router.routes]}"
)