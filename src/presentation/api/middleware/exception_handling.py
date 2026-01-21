from datetime import datetime, timezone
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

logger = structlog.get_logger()


class DebugExceptionMiddleware:
    """Middleware для отладки с выводом stack trace в ответах"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        response_headers = {}
        
        try:
            # Создаем кастомный send для перехвата ответа
            async def send_wrapper(message):
                if message.get("type") == "http.response.start":
                    response_headers.update({
                        k.decode(): v.decode() for k, v in message.get("headers", [])
                    })
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
            
        except RequestValidationError as exc:
            # Пропускаем RequestValidationError - он обрабатывается отдельным обработчиком
            raise exc
            
        except Exception as exc:
            # Логируем ошибку
            logger.error(
                "Unhandled exception",
                exc_info=exc,
                path=request.url.path,
                method=request.method,
                query_params=dict(request.query_params),
                client_host=request.client.host if request.client else None
            )
            
            # Формируем отладочный ответ
            response = await self._create_debug_response(exc, request)
            
            # Отправляем ответ
            await response(scope, receive, send)
    
    async def _create_debug_response(self, exc: Exception, request: Request) -> JSONResponse:
        """Создать отладочный ответ с полной информацией"""
        debug_info = {
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc().split('\n'),
            },
            "request": {
                "path": request.url.path,
                "method": request.method,
                "query_params": dict(request.query_params),
                "path_params": request.path_params,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "debug": True
        }
        
        # Добавляем тело запроса для POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    debug_info["request"]["body_preview"] = body[:1000].decode('utf-8', errors='ignore')
            except:
                debug_info["request"]["body_error"] = "Could not read request body"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=debug_info
        )