from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.orm import joinedload

from src.domain.entities import (
    Quote, Author, Category, Era, QuoteId
)
from src.domain.value_objects import QuoteText, Language, Rating
from src.domain.repositories import QuoteRepository, AuthorRepository
from src.infrastructure.database.models import (
    QuoteModel, AuthorModel, CategoryModel, EraModel
)


class SqlAlchemyQuoteRepository(QuoteRepository):
    def __init__(self, session):
        self.session = session

    def _to_domain(self, model: QuoteModel) -> Quote:
        """Преобразование модели SQLAlchemy в доменную сущность"""
        author = None
        if model.author:
            author = Author(
                id=model.author.id,
                name=model.author.name,
                birth_year=model.author.birth_year,
                death_year=model.author.death_year,
                bio=model.author.bio,
                created_at=model.author.created_at
            )
        
        return Quote(
            id=QuoteId(model.id),
            text=QuoteText(model.text),
            author=author,
            source=model.source,
            language=Language(model.language),
            rating=Rating(model.rating),
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, quote: Quote) -> QuoteModel:
        """Преобразование доменной сущности в модель SQLAlchemy"""
        def _ensure_naive(dt: Optional[datetime]) -> Optional[datetime]:
            """Преобразует aware datetime в naive, если необходимо"""
            if dt is None:
                return None
            if dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt
        
        return QuoteModel(
            id=quote.id.value,
            text=str(quote.text),
            author_id=quote.author.id if quote.author else None,
            source=quote.source,
            language=str(quote.language),
            rating=quote.rating.value,
            created_at=_ensure_naive(quote.created_at),
            updated_at=_ensure_naive(quote.updated_at),
        )

    async def get_by_id(self, quote_id: QuoteId) -> Optional[Quote]:
        stmt = (
            select(QuoteModel)
            .options(joinedload(QuoteModel.author))
            .where(QuoteModel.id == quote_id.value)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._to_domain(model) if model else None

    async def get_random(
        self,
        category: Optional[str] = None,
        era: Optional[str] = None,
        min_rating: int = 0,
        limit: int = 1
    ) -> List[Quote]:
        # Строим базовый запрос
        stmt = (
            select(QuoteModel)
            .options(joinedload(QuoteModel.author))
            .where(QuoteModel.rating >= min_rating)
            .order_by(func.random())  # PostgreSQL specific
            .limit(limit)
        )
        
        # Добавляем фильтры
        if category:
            stmt = stmt.join(CategoryModel).where(CategoryModel.name == category)
        if era:
            stmt = stmt.join(EraModel).where(EraModel.name == era)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_domain(model) for model in models]

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
        # Подсчет общего количества
        count_stmt = select(func.count(QuoteModel.id))
        stmt = (
            select(QuoteModel)
            .options(joinedload(QuoteModel.author))
            .limit(limit)
            .offset(offset)
        )
        
        # Применяем фильтры
        conditions = []
        
        if query:
            conditions.append(QuoteModel.text.ilike(f"%{query}%"))
        if author:
            conditions.append(AuthorModel.name.ilike(f"%{author}%"))
        if category:
            stmt = stmt.join(CategoryModel)
            count_stmt = count_stmt.join(CategoryModel)
            conditions.append(CategoryModel.name == category)
        if era:
            stmt = stmt.join(EraModel)
            count_stmt = count_stmt.join(EraModel)
            conditions.append(EraModel.name == era)
        if language:
            conditions.append(QuoteModel.language == str(language))
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))
        
        # Сортировка
        order_column = getattr(QuoteModel, sort_by, QuoteModel.rating)
        stmt = stmt.order_by(
            desc(order_column) if sort_desc else asc(order_column)
        )
        
        # Выполняем запросы
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_domain(model) for model in models], total

    async def save(self, quote: Quote) -> None:
        model = self._to_model(quote)
        self.session.add(model)

    async def save_many(self, quotes: List[Quote]) -> int:
        models = [self._to_model(quote) for quote in quotes]
        self.session.add_all(models)
        return len(models)

    async def update_rating(self, quote_id: QuoteId, increment: int) -> None:
        stmt = (
            select(QuoteModel)
            .where(QuoteModel.id == quote_id.value)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            model.rating += increment
            model.updated_at = datetime.now(timezone.utc)

    async def delete(self, quote_id: QuoteId) -> bool:
        stmt = (
            select(QuoteModel)
            .where(QuoteModel.id == quote_id.value)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            return True
        return False

    async def exists(self, text: str, author_name: Optional[str] = None) -> bool:
        stmt = select(func.count(QuoteModel.id)).where(QuoteModel.text == text)
        
        if author_name:
            stmt = (
                stmt
                .join(AuthorModel)
                .where(AuthorModel.name == author_name)
            )
        
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        
        return count > 0

    async def get_daily_quote(self) -> Optional[Quote]:
        """Получение цитаты дня (основано на дате)"""
        day_of_year = datetime.now().timetuple().tm_yday
        
        stmt = (
            select(QuoteModel)
            .options(joinedload(QuoteModel.author))
            .order_by(QuoteModel.id)  # Для детерминированности
            .offset(day_of_year % 1000)  # Простая логика на основе дня года
            .limit(1)
        )
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._to_domain(model) if model else None


class SqlAlchemyAuthorRepository(AuthorRepository):
    def __init__(self, session):
        self.session = session

    async def get_by_id(self, author_id: UUID) -> Optional[Author]:
        stmt = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            return Author(
                id=model.id,
                name=model.name,
                birth_year=model.birth_year,
                death_year=model.death_year,
                bio=model.bio,
                created_at=model.created_at
            )
        return None

    async def find_by_name(self, name: str) -> Optional[Author]:
        stmt = select(AuthorModel).where(AuthorModel.name.ilike(name))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            return Author(
                id=model.id,
                name=model.name,
                birth_year=model.birth_year,
                death_year=model.death_year,
                bio=model.bio,
                created_at=model.created_at
            )
        return None

    async def save(self, author: Author) -> None:
        def _ensure_naive(dt: Optional[datetime]) -> Optional[datetime]:
            if dt is None:
                return None
            if dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt
        
        model = AuthorModel(
            id=author.id,
            name=author.name,
            birth_year=author.birth_year,
            death_year=author.death_year,
            bio=author.bio,
            created_at=_ensure_naive(author.created_at)
        )
        self.session.add(model)