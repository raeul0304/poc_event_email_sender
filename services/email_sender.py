import json
from pathlib import Path
from typing import Any
from langchain_mcp_adapters.client import MultiServerMCPClient

BASE_DIR = Path(__file__).resolve().parent
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



async def send_email(to: str | list[str], subject: str, body: str, *, cc: str | list[str] | None = None, bcc: str | list[str] | None = None, config_path: str | Path = DEFAULT_CONFIG_PATH):
    """MCP 서버를 통해 이메일 발송"""

    send_email_tool = await get_send_email_tool(config_path)

    payload: dict[str, Any] = {
        "to": to if isinstance(to, list) else [to],
        "subject": subject,
        "body": body,
    }

    if cc is not None:
        payload["cc"] = cc if isinstance(cc, list) else [cc]
    if bcc is not None:
        payload["bcc"] = bcc if isinstance(bcc, list) else [bcc]

    try:
        return await send_email_tool.ainvoke(payload)

    except Exception as exc:
        raise RuntimeError(
            f"이메일 발송 중 오류가 발생했습니다: {exc}"
        ) from exc