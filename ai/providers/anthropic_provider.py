"""Anthropic Claude provider."""

from __future__ import annotations
import os
from typing import Any

from ai.providers.base import BaseLLMProvider, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.model   = config.get("model", "claude-sonnet-4-6")
        self._api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY", "")
        self._client  = None

    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic  # noqa: PLC0415
                self._client = anthropic.Anthropic(api_key=self._api_key)
            except ImportError:
                raise RuntimeError("anthropic package not installed: pip install anthropic")
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
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        content = msg.content[0].text
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=msg.usage.input_tokens,
            tokens_out=msg.usage.output_tokens,
            raw=msg,
        )
