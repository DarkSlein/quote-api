from contextlib import asynccontextmanager
import json
import traceback
from fastapi import FastAPI, HTTPException, Request
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
        debug=settings.DEBUG,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Логируем ошибку
        error_traceback = traceback.format_exc()
        print(f"\n{'='*60}")
        print(f"ERROR: {type(exc).__name__}")
        print(f"Message: {exc}")
        print(f"Path: {request.url.path}")
        print(f"Method: {request.method}")
        print(f"Traceback:\n{error_traceback}")
        print(f"{'='*60}\n")
        
        status_code = 500
        
        # Определяем статус код
        if isinstance(exc, HTTPException):
            status_code = exc.status_code
        elif isinstance(exc, RequestValidationError):
            status_code = 422
        
        # Формируем ответ
        response_content = {
            "detail": str(exc),
            "type": type(exc).__name__,
        }
        
        # Добавляем debug информацию
        if settings.DEBUG and settings.SHOW_TRACEBACK:
            response_content.update({
                "debug": {
                    "traceback": error_traceback.split('\n'),
                    "path": request.url.path,
                    "method": request.method,
                    "request_body": await _get_request_body(request),
                }
            })
        
        return JSONResponse(
            status_code=status_code,
            content=response_content
        )

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler
    )

    if settings.DEBUG:
        app.add_middleware(DebugExceptionMiddleware, debug=True)
    

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

async def _get_request_body(request: Request):
    """Получить тело запроса для отладки"""
    try:
        body = await request.body()
        if body:
            try:
                return json.loads(body.decode('utf-8'))
            except:
                return body.decode('utf-8')[:500]
    except:
        pass
    return None

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