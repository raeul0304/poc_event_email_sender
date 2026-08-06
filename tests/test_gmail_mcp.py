import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient


def create_server_config() -> dict:
    return {
        "gmail": {
            "transport": "stdio",
            "command": "npx.cmd",
            "args": [
                "-y",
                "@gongrzhe/server-gmail-autoauth-mcp",
            ],
        }
    }


async def test_send_email() -> None:
    client = MultiServerMCPClient(create_server_config())

    tools = await client.get_tools()

    print("연결된 MCP Tools:")
    for tool in tools:
        print(f"- {tool.name}")

    send_email = next(
        (tool for tool in tools if tool.name == "send_email"),
        None,
    )

    if send_email is None:
        raise RuntimeError("send_email Tool을 찾을 수 없습니다.")

    result = await send_email.ainvoke(
        {
            # 최초 테스트는 본인 이메일 주소 권장
            "to": ["sbtgloballab@gmail.com"],
            "subject": "[PoC 테스트] Gmail MCP 메일 발송",
            "body": (
                "안녕하세요.\n\n"
                "Gmail MCP Server 연결 및 메일 발송 테스트입니다.\n"
                "이 메일이 도착했다면 OAuth 인증과 MCP 연결이 정상입니다.\n\n"
                "감사합니다."
            ),
        }
    )

    print("\n메일 발송 결과:")
    print(result)


if __name__ == "__main__":
    asyncio.run(test_send_email())