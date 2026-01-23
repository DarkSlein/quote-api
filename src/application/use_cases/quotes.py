from typing import Optional, List, Tuple

import structlog

from src.application.services.external_quote_service import ExternalQuoteService
from src.domain.entities import Quote, Author, QuoteId
from src.domain.repositories import UnitOfWork
from src.domain.value_objects import QuoteText, Language, UpdateResult, QuoteSource
from src.domain.exceptions import (
    QuoteNotFoundException,
    QuoteAlreadyExistsException
)


logger = structlog.get_logger()

class GetQuoteUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, quote_id: QuoteId) -> Quote:
        async with self.uow:
            quote = await self.uow.quotes.get_by_id(quote_id)
            if not quote:
                raise QuoteNotFoundException(f"Quote {quote_id} not found")
            return quote


class GetRandomQuoteUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self,
        category: Optional[str] = None,
        era: Optional[str] = None,
        min_rating: int = 0,
        limit: int = 1
    ) -> List[Quote]:
        async with self.uow:
            return await self.uow.quotes.get_random(category, era, min_rating, limit)


class SearchQuotesUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self,
        query: Optional[str] = None,
        author: Optional[str] = None,
        category: Optional[str] = None,
        era: Optional[str] = None,
        language: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "rating",
        sort_desc: bool = True
    ) -> Tuple[List[Quote], int, int]:
        async with self.uow:
            offset = (page - 1) * page_size
            lang = Language(language) if language else None
            
            quotes, total = await self.uow.quotes.search(
                query=query,
                author=author,
                category=category,
                era=era,
                language=lang,
                limit=page_size,
                offset=offset,
                sort_by=sort_by,
                sort_desc=sort_desc
            )
            
            total_pages = (total + page_size - 1) // page_size if total > 0 else 1
            return quotes, total, total_pages


class CreateQuoteUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self,
        text: str,
        author_name: Optional[str] = None,
        category_name: Optional[str] = None,
        era_name: Optional[str] = None,
        source: Optional[str] = None,
        language: str = "ru"
    ) -> Quote:
        async with self.uow:
            # Проверяем, существует ли уже такая цитата
            exists = await self.uow.quotes.exists(text, author_name)
            if exists:
                raise QuoteAlreadyExistsException("Quote already exists")

            # Ищем или создаем автора
            author = None
            if author_name:
                author = await self.uow.authors.find_by_name(author_name)
                if not author:
                    author = Author(name=author_name)
                    await self.uow.authors.save(author)

            # Создаем цитату
            quote = Quote(
                text=QuoteText(text),
                author=author,
                source=source,
                language=Language(language)
            )

            await self.uow.quotes.save(quote)
            await self.uow.commit()
            
            return quote


class RateQuoteUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, quote_id: QuoteId, increment: int = 1) -> Quote:
        async with self.uow:
            quote = await self.uow.quotes.get_by_id(quote_id)
            if not quote:
                raise QuoteNotFoundException(f"Quote {quote_id} not found")

            quote.rate(increment)
            await self.uow.quotes.update_rating(quote_id, increment)
            await self.uow.commit()
            
            return quote


class UpdateQuotesFromExternalSourceUseCase:
    def __init__(self, uow: UnitOfWork, external_service: ExternalQuoteService):
        self.uow = uow
        self.external_service = external_service

    async def execute(self, source: QuoteSource) -> UpdateResult:
        added = 0
        updated = 0
        errors = 0

        async with self.uow:
            try:
                external_quotes = await self.external_service.fetch_quotes(source)
                
                for external_quote in external_quotes:
                    try:
                        quote_text = external_quote.text_str
                        author_name = external_quote.author.name if external_quote.author else None

                        # Проверяем, существует ли уже
                        exists = await self.uow.quotes.exists(quote_text, author_name)
                        
                        if not exists:
                            await self.uow.quotes.save(external_quote)
                            added += 1
                        else:
                            updated += 1
                            
                    except Exception as e:
                        logger.error("Failed to save quote", quote=external_quote, error=str(e))
                        errors += 1
                        # Логируем ошибку, но продолжаем обработку
                        continue
                
                await self.uow.commit()
                return UpdateResult(
                    source=source,
                    added=added,
                    updated=updated,
                    errors=errors
                )
                
            except Exception as e:
                await self.uow.rollback()
                raise

class DeleteQuoteUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, quote_id: QuoteId) -> bool:
        """Удаляет цитату по ID. Возвращает True если удалено, False если не найдено."""
        async with self.uow:
            # Проверяем существование цитаты (опционально, но рекомендуется)
            existing_quote = await self.uow.quotes.get_by_id(quote_id)
            if not existing_quote:
                raise QuoteNotFoundException(f"Quote {quote_id} not found")
            
            # Удаляем цитату
            deleted = await self.uow.quotes.delete(quote_id)
            if deleted:
                await self.uow.commit()
            return deleted