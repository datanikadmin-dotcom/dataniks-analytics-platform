"""OpenAI provider."""

from __future__ import annotations
import os
from typing import Any

from ai.providers.base import BaseLLMProvider, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.model   = config.get("model", "gpt-4o")
        self._api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY", "")
        self._client  = None

    @property
    def client(self):
        if self._client is None:
            try:
                import openai  # noqa: PLC0415
                self._client = openai.OpenAI(api_key=self._api_key)
            except ImportError:
                raise RuntimeError("openai package not installed: pip install openai")
        return self._client

    def is_available(self) -> bool:
        return bool(self._api_key)

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
        )
        content = response.choices[0].message.content
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
            raw=response,
        )
