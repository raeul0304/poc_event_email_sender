import json
import asyncio
import os
from pathlib import Path
from typing import Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from schemas import EmailResult


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.json"


def load_server_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """config.json 파일을 읽어 MCP 서버 설정을 로드"""

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    return config



async def get_send_email_tool(config_path: str | Path = DEFAULT_CONFIG_PATH):
    """MCP 서버에 연결하여 send_email Tool을 가져옴"""

    config = load_server_config(config_path)
    client = MultiServerMCPClient(config)
    tools = await client.get_tools()

    send_email_tool = next(
        (tool for tool in tools if tool.name == "send_email"),
        None,
    )

    if send_email_tool is None:
        available_tools = [tool.name for tool in tools]

        raise RuntimeError(f"send_email Tool을 찾을 수 없습니다. 현재 사용 가능한 Tool 목록: {available_tools}")

    return send_email_tool



async def send_email(to: str | list[str], subject: str, body: str, *, html_body: str | None = None, config_path: str | Path = DEFAULT_CONFIG_PATH):
    """MCP 서버를 통해 이메일 발송"""

    try:
        send_email_tool = await get_send_email_tool(config_path)
        raw_recipients = to if isinstance(to, list) else [to]
        recipients = [
            address.strip()
            for address in raw_recipients
            if isinstance(address, str) and address.strip()
        ]

        if html_body:
            payload = {
                "to": recipients,
                "subject": subject,
                "body": body,
                "htmlBody": html_body,
                "mimeType": "text/html",
            }
        else:
            payload = {
                "to":recipients,
                "subject": subject,
                "body": body,
                "mimeType": "text/plain",
            }

        #print("[DEBUG] payload =", payload)

        raw = await send_email_tool.ainvoke(payload)
        print(f"\n\n [DEBUG] Gmail MCP raw 응답 : {raw}")
        return EmailResult(success=True, message="이메일 발송 성공", raw=raw)

    except Exception as exc:
        return EmailResult(success=False, message=str(exc), raw=None)




async def main():
    print("=== MCP 이메일 HTML 전송 테스트 ===")

    result = await send_email(
        to="sbtgloballab@gmail.com",
        subject="[TEST] HTML 이메일 테스트",
        body="HTML 메일 테스트입니다.",
        html_body="""
        <!doctype html>
        <html>
        <body>
            <h2>행사 참가 안내</h2>
            <p>HTML 이메일 테스트입니다.</p>

            <div style="
                border:1px solid #ddd;
                padding:16px;
                border-radius:8px;
            ">
                <strong>가공배전 교육</strong><br>
                주최: 대한전기협회<br>
                기간: 2026-08-10 ~ 2026-09-18
            </div>
        </body>
        </html>
        """,
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())