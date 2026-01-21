from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from src.shared.config import settings


class Database:
    def __init__(self):
        db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        
        self.engine = create_async_engine(
            db_url,
            echo=settings.SQL_ECHO,
            poolclass=NullPool if settings.TESTING else None,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Контекстный менеджер для сессии БД"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def disconnect(self):
        """Закрытие соединения с БД"""
        await self.engine.dispose()


# Глобальный экземпляр БД
database = Database()