from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from uuid import UUID

from src.domain.entities import Quote, Author, QuoteId
from src.domain.value_objects import Language


class QuoteRepository(ABC):
    @abstractmethod
    async def get_by_id(self, quote_id: QuoteId) -> Optional[Quote]:
        pass

    @abstractmethod
    async def get_random(
        self,
        category: Optional[str] = None,
        era: Optional[str] = None,
        min_rating: int = 0,
        limit: int = 1
    ) -> List[Quote]:
        pass

    @abstractmethod
    async def search(
        self,
        query: Optional[str] = None,
        author: Optional[str] = None,
        category: Optional[str] = None,
        era: Optional[str] = None,
        language: Optional[Language] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "rating",
        sort_desc: bool = True
    ) -> Tuple[List[Quote], int]:
        pass

    @abstractmethod
    async def save(self, quote: Quote) -> None:
        pass

    @abstractmethod
    async def save_many(self, quotes: List[Quote]) -> int:
        pass

    @abstractmethod
    async def update_rating(self, quote_id: QuoteId, increment: int) -> None:
        pass

    @abstractmethod
    async def delete(self, quote_id: QuoteId) -> bool:
        pass

    @abstractmethod
    async def exists(self, text: str, author_name: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    async def get_daily_quote(self) -> Optional[Quote]:
        pass


class AuthorRepository(ABC):
    @abstractmethod
    async def get_by_id(self, author_id: UUID) -> Optional[Author]:
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Author]:
        pass

    @abstractmethod
    async def save(self, author: Author) -> None:
        pass


class UnitOfWork(ABC):
    """Паттерн Unit of Work для управления транзакциями"""

    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass

    @property
    @abstractmethod
    def quotes(self) -> QuoteRepository:
        pass

    @property
    @abstractmethod
    def authors(self) -> AuthorRepository:
        pass