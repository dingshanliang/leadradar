from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str | None = None
    published_at: str | None = None


@dataclass(frozen=True)
class RawPage:
    url: str
    status_code: int
    content_type: str | None
    text: str


class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        pass


class FetchProvider(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> RawPage:
        pass


class DocumentParser(ABC):
    @abstractmethod
    def extract_text(self, page: RawPage) -> str:
        pass
