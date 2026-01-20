from typing import AsyncGenerator

from src.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


async def get_uow() -> AsyncGenerator[SqlAlchemyUnitOfWork, None]:
    """Dependency для получения Unit of Work"""
    async with SqlAlchemyUnitOfWork() as uow:
        yield uow