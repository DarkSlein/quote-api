from typing import Any, Optional

from domain.repositories import UnitOfWork, QuoteRepository, AuthorRepository
from infrastructure.repositories.sqlalchemy_repositories import (
    SqlAlchemyQuoteRepository,
    SqlAlchemyAuthorRepository
)
from infrastructure.database.session import database


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self):
        self.session = None
        self._quotes: Optional[QuoteRepository] = None
        self._authors: Optional[AuthorRepository] = None

    async def __aenter__(self):
        self.session = database.session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        if self.session:
            await self.session.close()

    @property
    def quotes(self) -> QuoteRepository:
        if self._quotes is None:
            self._quotes = SqlAlchemyQuoteRepository(self.session)
        return self._quotes

    @property
    def authors(self) -> AuthorRepository:
        if self._authors is None:
            self._authors = SqlAlchemyAuthorRepository(self.session)
        return self._authors

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()