# 설정에 따라 적합한 모델 객체 생성
from models.base import BaseLLM
from models.openai_adapter import OpenAIAdapter
from models.claude_adapter import ClaudeAdapter


def load_llm(provider: str, model: str, api_key: str | None = None) -> BaseLLM:
    provider = provider.strip().casefold()

    if provider == "openai":
        return OpenAIAdapter(model=model, api_key=api_key)
    if provider == "claude":
        return ClaudeAdapter(model=model, api_key=api_key)

    raise ValueError(f"지원되지 않는 LLM provider: {provider}")