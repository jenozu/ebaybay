from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AIProviderError(RuntimeError):
    pass


class AIConfigurationError(AIProviderError):
    pass


@dataclass(frozen=True)
class AIImage:
    path: Path
    mime_type: str


@dataclass(frozen=True)
class ProviderResult:
    raw_json: str
    response_payload: dict[str, Any]


class AIProvider(ABC):
    name = "unknown"
    model = "unknown"

    @abstractmethod
    def analyze(self, images: list[AIImage], seller_notes: str | None) -> ProviderResult:
        raise NotImplementedError
