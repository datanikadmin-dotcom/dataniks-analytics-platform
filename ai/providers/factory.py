"""Provider factory — select LLM backend from config/env."""

from __future__ import annotations
import os
from typing import Any

from ai.providers.base import BaseLLMProvider


def get_provider(config: dict[str, Any] | None = None) -> BaseLLMProvider:
    """
    Return the configured LLM provider.

    Resolution order:
      1. config["provider"]
      2. AI_PROVIDER env var
      3. "mock" (safe default for development)
    """
    cfg = config or {}
    provider_name = (
        cfg.get("provider")
        or os.getenv("AI_PROVIDER", "mock")
    ).lower()

    if provider_name == "mock":
        from ai.providers.mock import MockProvider
        return MockProvider(config=cfg)

    if provider_name == "anthropic":
        from ai.providers.anthropic_provider import AnthropicProvider
        p = AnthropicProvider(config=cfg)
        if not p.is_available():
            raise RuntimeError(
                "AnthropicProvider requires ANTHROPIC_API_KEY. "
                "Set it in .env or use AI_PROVIDER=mock for development."
            )
        return p

    if provider_name == "openai":
        from ai.providers.openai_provider import OpenAIProvider
        p = OpenAIProvider(config=cfg)
        if not p.is_available():
            raise RuntimeError(
                "OpenAIProvider requires OPENAI_API_KEY. "
                "Set it in .env or use AI_PROVIDER=mock for development."
            )
        return p

    raise ValueError(
        f"Unknown AI provider: '{provider_name}'. "
        "Valid options: mock | anthropic | openai"
    )
