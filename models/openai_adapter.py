from __future__ import annotations
from openai import OpenAI
from models.base import BaseLLM, ResponseType

class OpenAIAdapter(BaseLLM):
    def __init__(self, model: str, api_key: str | None = None):
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def generate(self, system_prompt, user_prompt, response_schema : type[ResponseType]) -> ResponseType:
        if not system_prompt.strip() or not user_prompt.strip():
            raise ValueError("system_prompt와 user_prompt는 비어있을 수 없습니다.")

        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            text_format=response_schema
        )

        parsed_response = response.output_parsed
        print(f"[Debug] OpenAI 응답: {parsed_response}")
        return parsed_response