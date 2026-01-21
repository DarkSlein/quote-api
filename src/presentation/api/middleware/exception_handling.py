from datetime import datetime, timezone
import traceback
from fastapi import Request, status, HTTPException
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
            # Пытаемся выполнить запрос
            await self.app(scope, receive, send)
            
        except HTTPException as exc:
            # Перехватываем HTTPException
            if self.debug:
                response = self._create_http_exception_response(exc, request)
            else:
                response = JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail}
                )
            await response(scope, receive, send)
            
        except RequestValidationError as exc:
            # Перехватываем RequestValidationError
            # Передаем дальше - у нас есть отдельный обработчик
            raise exc
            
        except Exception as exc:
            # Перехватываем все остальные исключения
            if self.debug:
                response = self._create_debug_response(exc, request)
            else:
                response = JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Internal server error"}
                )
            await response(scope, receive, send)
    
    def _create_http_exception_response(self, exc: HTTPException, request: Request) -> JSONResponse:
        """Создать отладочный ответ для HTTPException"""
        traceback_str = traceback.format_exc()
        
        # Логируем в консоль Render
        print(f"\n{'='*60}")
        print(f"HTTP EXCEPTION: {type(exc).__name__}: {exc.detail}")
        print(f"PATH: {request.url.path}")
        print(f"METHOD: {request.method}")
        print(f"STATUS CODE: {exc.status_code}")
        print(f"TRACEBACK:\n{traceback_str}")
        print(f"{'='*60}\n")
        
        content = {
            "detail": exc.detail,
            "type": type(exc).__name__,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "debug": True
        }
        
        # Добавляем traceback только если он есть и не пустой
        if traceback_str and "NoneType: None" not in traceback_str:
            content["traceback"] = traceback_str.split('\n')
        
        return JSONResponse(
            status_code=exc.status_code,
            content=content
        )
    
    def _create_debug_response(self, exc: Exception, request: Request) -> JSONResponse:
        """Создать отладочный ответ с полной информацией"""
        traceback_str = traceback.format_exc()
        
        # Логируем в консоль Render
        print(f"\n{'='*60}")
        print(f"UNHANDLED EXCEPTION: {type(exc).__name__}: {exc}")
        print(f"PATH: {request.url.path}")
        print(f"METHOD: {request.method}")
        print(f"TRACEBACK:\n{traceback_str}")
        print(f"{'='*60}\n")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback_str.split('\n'),
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "debug": True
            }
        )