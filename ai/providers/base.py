"""Abstract LLM provider interface — all providers implement this."""

from __future__ import annotations
import abc
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    content: str
    model:   str
    tokens_in:  int = 0
    tokens_out: int = 0
    raw:     Any = None


class BaseLLMProvider(abc.ABC):
    """Provider-agnostic interface for LLM completions."""

    provider_name: str = "base"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.model  = config.get("model", "")

    @abc.abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> LLMResponse: ...

    @abc.abstractmethod
    def is_available(self) -> bool: ...
