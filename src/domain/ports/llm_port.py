"""LLM クライアントのインターフェース"""

from typing import AsyncIterator, Protocol, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class ChatResponse(BaseModel):
    """LLM の応答"""

    model_config = {"frozen": True}

    content: str = Field(description="LLM の応答テキスト")
    thinking: str = Field(default="", description="Thinking ログ（推論過程）")


class LLMPort(Protocol):
    """LLM クライアントのインターフェース"""

    async def agenerate(
        self,
        messages: list[dict],
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> ChatResponse:
        """テキスト生成（summarize 等で使用）"""
        ...

    async def agenerate_structured(
        self,
        messages: list[dict],
        response_model: type[T],
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> T:
        """構造化出力（task_planning, judge で使用）"""
        ...

    async def astream(
        self,
        messages: list[dict],
        *,
        reasoning: str | None = None,
    ) -> AsyncIterator[str]:
        """ストリーミング生成（generate_answer で使用）"""
        ...
