from __future__ import annotations
import os
import json, re
from openai import OpenAI
from models.base import BaseLLM, ResponseType


class ClaudeAdapter(BaseLLM):
    def __init__(self, model: str, api_key: str | None = None):
        self.model = model
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

    def generate(self, system_prompt: str, user_prompt: str, response_schema: type[ResponseType]) -> ResponseType:
        if not system_prompt.strip() or not user_prompt.strip():
            raise ValueError("system_prompt와 user_prompt는 비어있을 수 없습니다.")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        content = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if not json_match:
            raise ValueError(f"JSON을 찾을 수 없습니다. 원본 응답: {content[:200]}")

        content = json_match.group()
        parsed = response_schema.model_validate(json.loads(content))

        print(f"[Claude] model={self.model}, tokens={response.usage.total_tokens}")

        return parsed