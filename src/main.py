from contextlib import asynccontextmanager
import traceback
from urllib.parse import unquote_plus
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import structlog
import asyncio

from src.application.background_tasks.quote_miner import QuoteMiner
from src.shared.config import settings
from src.infrastructure.database.session import database
from src.infrastructure.database.models import Base
import src.presentation.api.v1.quotes as quotes
import src.presentation.api.v1.admin as admin
from src.presentation.api.middleware.exception_handling import DebugExceptionMiddleware
from src.presentation.api.middleware.validation_handler import validation_exception_handler

logger = structlog.get_logger()


def patch_fastapi_url_decoding():
    """Патчим FastAPI для автоматического декодирования плюсов в query параметрах"""
    from fastapi.datastructures import QueryParams
    
    original_init = QueryParams.__init__
    
    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        
        # Декодируем все значения
        decoded_items = []
        for key, value in self._dict.items():
            if isinstance(value, str):
                decoded_value = unquote_plus(value.replace('+', ' '))
                decoded_items.append((key, decoded_value))
            elif isinstance(value, list):
                decoded_list = [
                    unquote_plus(v.replace('+', ' ')) if isinstance(v, str) else v
                    for v in value
                ]
                decoded_items.append((key, decoded_list))
            else:
                decoded_items.append((key, value))
        
        # Обновляем внутренний словарь
        self._dict = dict(decoded_items)
    
    QueryParams.__init__ = patched_init

patch_fastapi_url_decoding()

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
        debug=settings.DEBUG,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Регистрируем обработчики исключений
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler
    )
    
    # Добавляем middleware для отладки (сначала DebugExceptionMiddleware)
    app.add_middleware(DebugExceptionMiddleware, debug=settings.DEBUG)
    
    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    
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