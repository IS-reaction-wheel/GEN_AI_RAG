"""Ollama LLM アダプタ（LLMPort の実装）"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import TypeVar

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from domain.ports.llm_port import ChatResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OllamaAdapter:
    """Ollama / LangChain を使用した LLMPort の具体実装"""

    def __init__(
        self,
        model_name: str,
        num_ctx: int = 16384,
        temperature: float = 0.8,
        top_k: int = 40,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1,
    ) -> None:
        self._model_name = model_name
        self._num_ctx = num_ctx
        self._temperature = temperature
        self._top_k = top_k
        self._top_p = top_p
        self._repeat_penalty = repeat_penalty

    def _make_llm(
        self,
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> ChatOllama:
        """パラメータを上書きした ChatOllama インスタンスを生成する。"""
        kwargs: dict = {
            "model": self._model_name,
            "num_ctx": self._num_ctx,
            "temperature": self._temperature,
            "top_k": self._top_k,
            "top_p": self._top_p,
            "repeat_penalty": self._repeat_penalty,
        }
        if num_predict is not None:
            kwargs["num_predict"] = num_predict
        if reasoning is not None:
            kwargs["reasoning"] = reasoning
        return ChatOllama(**kwargs)

    @staticmethod
    def _to_langchain_messages(
        messages: list[dict],
    ) -> list[SystemMessage | HumanMessage | AIMessage]:
        """list[dict] を LangChain メッセージに変換する。"""
        result: list[SystemMessage | HumanMessage | AIMessage] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                result.append(SystemMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
            else:
                result.append(HumanMessage(content=content))
        return result

    async def agenerate(
        self,
        messages: list[dict],
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> ChatResponse:
        """テキスト生成"""
        llm = self._make_llm(num_predict=num_predict, reasoning=reasoning)
        lc_messages = self._to_langchain_messages(messages)
        result = await llm.ainvoke(lc_messages)

        content = result.content if isinstance(result.content, str) else ""
        thinking = ""
        if hasattr(result, "additional_kwargs"):
            thinking = result.additional_kwargs.get("reasoning_content", "")

        return ChatResponse(content=content, thinking=thinking)

    async def agenerate_structured(
        self,
        messages: list[dict],
        response_model: type[T],
        *,
        num_predict: int | None = None,
        reasoning: str | None = None,
    ) -> T:
        """構造化出力"""
        llm = self._make_llm(num_predict=num_predict, reasoning=reasoning)
        structured_llm = llm.with_structured_output(response_model)
        lc_messages = self._to_langchain_messages(messages)
        return await structured_llm.ainvoke(lc_messages)

    async def astream(
        self,
        messages: list[dict],
        *,
        reasoning: str | None = None,
    ) -> AsyncIterator[str]:
        """ストリーミング生成"""
        llm = self._make_llm(reasoning=reasoning)
        lc_messages = self._to_langchain_messages(messages)
        async for chunk in llm.astream(lc_messages):
            if isinstance(chunk.content, str) and chunk.content:
                yield chunk.content
