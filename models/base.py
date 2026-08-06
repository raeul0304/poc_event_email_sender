# 모든 모델이 따라야 하는 공통 사용 규칙
from abc import ABC, abstractmethod
from typing import TypeVar
from pydantic import BaseModel

ResponseType = TypeVar("ResponseType", bound=BaseModel)

class BaseLLM(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, response_schema: type[ResponseType]) -> ResponseType:
        ...