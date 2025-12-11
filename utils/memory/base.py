"""Abstract memory store definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class MemoryStore(ABC):
    """Defines the interface for memory stores."""

    @abstractmethod
    async def add(self, key: str, value: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def read(self, key: str) -> Optional[Any]:
        raise NotImplementedError()
