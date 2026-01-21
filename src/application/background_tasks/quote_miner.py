import asyncio
import structlog

from src.domain.value_objects import QuoteSource
from src.application.use_cases.quotes import UpdateQuotesFromExternalSourceUseCase
from src.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from src.application.services.external_quote_service import ExternalQuoteService

logger = structlog.get_logger()


class QuoteMiner:
    """Фоновая задача для обновления цитат из внешних источников"""
    
    def __init__(self, update_interval: int = 3600):  # 1 час по умолчанию
        self.update_interval = update_interval
        self.is_running = False

    async def start(self):
        """Запуск фоновой задачи"""
        self.is_running = True
        logger.info("Quote miner started", interval=self.update_interval)
        
        while self.is_running:
            try:
                await self._update_all_sources()
            except Exception as e:
                logger.error("Error in quote miner", error=str(e))
            
            await asyncio.sleep(self.update_interval)

    async def stop(self):
        """Остановка фоновой задачи"""
        self.is_running = False
        logger.info("Quote miner stopped")

    async def _update_all_sources(self):
        """Обновление из всех источников"""
        sources = [QuoteSource.WIKIQUOTE, QuoteSource.FORISMATIC]
        
        async with SqlAlchemyUnitOfWork() as uow:
            async with ExternalQuoteService() as external_service:
                update_use_case = UpdateQuotesFromExternalSourceUseCase(
                    uow, external_service
                )
                
                for source in sources:
                    try:
                        result = await update_use_case.execute(source)
                        logger.info(
                            "Quotes updated from source",
                            source=source.value,
                            added=result.added,
                            updated=result.updated,
                            errors=result.errors,
                            success_rate=f"{result.success_rate:.1f}%"
                        )
                    except Exception as e:
                        logger.error(
                            "Failed to update from source",
                            source=source.value,
                            error=str(e)
                        )

    async def update_now(self) -> dict:
        """Немедленное обновление (для вызова из API)"""
        results = {}
        
        async with SqlAlchemyUnitOfWork() as uow:
            async with ExternalQuoteService() as external_service:
                update_use_case = UpdateQuotesFromExternalSourceUseCase(
                    uow, external_service
                )
                
                for source in QuoteSource:
                    try:
                        result = await update_use_case.execute(source)
                        results[source.value] = {
                            "added": result.added,
                            "updated": result.updated,
                            "errors": result.errors,
                            "success_rate": result.success_rate
                        }
                    except Exception as e:
                        results[source.value] = {"error": str(e)}
        
        return results