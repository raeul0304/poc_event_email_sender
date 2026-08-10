import os
import asyncio
from fastapi import APIRouter, Header, HTTPException, Depends
from schemas import MailSchedulerRunRequest, MailSchedulerRunResponse
from services.event_filter_client import fetch_events_by_filter

router = APIRouter(prefix="/api/mail-schedulers")

# @router.post("/run")
# async def run_mail_scheduler():
#     return {"status": "ok"}


def verify_internal_key(x_internal_service_key: str = Header(...)):
    """scheduler sent X-internal-Service-Key 검증"""
    expected = os.getenv("INTERNAL_SERVICE_KEY")
    if x_internal_service_key != expected:
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")



async def process_schedule(schedule) -> str:
    """스케줄별 처리"""
    try: 
        filter_dict = schedule.filter.model_dump()
        events = await fetch_events_by_filter(filter_dict)

        if not events:
            print(f"[Debug] {schedule.mail_scheduler_id} → 매칭 행사 없음 (skipped)")
            return "skipped"

        print(f"[Debug] {schedule.mail_scheduler_id} → {len(events)}건 매칭")
        return "sent"

    except Exception as e:
        print(f"[Error] {schedule.mail_scheduler_id} 처리 실패: {e}")
        return "failed"



@router.post("/run", response_model=MailSchedulerRunResponse)
async def run_mail_scheduler(request: MailSchedulerRunRequest, _: None = Depends(verify_internal_key)):
    print(f"[Debug] 수신된 스케줄 수: {len(request.schedules)}")

    results = await asyncio.gather(
        *[process_schedule(schedule) for schedule in request.schedules]
    )

    print(f"[Debug] 처리 결과: {results}")

    if all(r == "sent" for r in results):
        status = "ok"
    elif all(r == "failed" for r in results):
        status = "failed"
    else:
        status = "partial"

    return MailSchedulerRunResponse(status=status)




print(">>>>>> mail_schedulers 라우터 로드됨")
print(
    f">>>>>>>>>> mail_schedulers 등록 라우트: "
    f"{[(r.path, r.methods) for r in router.routes]}"
)