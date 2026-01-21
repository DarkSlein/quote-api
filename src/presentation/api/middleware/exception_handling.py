from datetime import datetime, timezone
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

logger = structlog.get_logger()


class DebugExceptionMiddleware:
    """Middleware для отладки с выводом stack trace в ответах"""
    
    def __init__(self, app, debug: bool = False):
        self.app = app
        self.debug = debug
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Логируем ошибку
            logger.error(
                "Unhandled exception",
                exc_info=exc,
                path=request.url.path,
                method=request.method
            )
            
            # Формируем ответ
            if self.debug:
                response = self._create_debug_response(exc)
            else:
                response = self._create_production_response(exc)
            
            await response(scope, receive, send)
    
    def _create_debug_response(self, exc: Exception) -> JSONResponse:
        """Создать отладочный ответ с полной информацией"""
        error_detail = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc().split('\n'),
        }
        
        # Добавляем дополнительную информацию для ValidationError
        if isinstance(exc, RequestValidationError):
            error_detail["validation_errors"] = exc.errors()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": error_detail,
                "debug": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    def _create_production_response(self, exc: Exception) -> JSONResponse:
        """Создать продакшен-ответ без деталей"""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            }
        )