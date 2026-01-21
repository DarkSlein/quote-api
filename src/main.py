from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
import structlog
import asyncio

from src.application.background_tasks.quote_miner import QuoteMiner
from src.shared.config import settings
from src.infrastructure.database.session import database
from src.infrastructure.database.models import Base
import src.presentation.api.v1.quotes as quotes
import src.presentation.api.v1.admin as admin
#from src.presentation.api.middleware import (
#    LoggingMiddleware,
#    ExceptionMiddleware,
#    RateLimitMiddleware
#)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекстный менеджер жизненного цикла приложения"""
    # Startup
    logger.info("Starting Quote API", version=settings.VERSION)
    
    # Проверяем подключение к БД
    try:
        async with database.get_session() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        raise

    # Создаем таблицы, если они не существуют
    try:
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create tables", error=str(e))
        # Не падаем, возможно таблицы уже созданы

    # Запускаем фоновые задачи
    if not settings.TESTING:
        miner = QuoteMiner(update_interval=settings.UPDATE_INTERVAL)
        asyncio.create_task(miner.start())
        logger.info("Background quote miner started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Quote API")
    await database.disconnect()


def create_application() -> FastAPI:
    """Фабрика для создания FastAPI приложения"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    #app.add_middleware(LoggingMiddleware)
    #app.add_middleware(ExceptionMiddleware)
    #app.add_middleware(RateLimitMiddleware)
    
    # Роутеры
    app.include_router(quotes.router, prefix=settings.API_V1_STR)
    app.include_router(admin.router, prefix=settings.API_V1_STR)
    
    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.PROJECT_NAME}
    
    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )