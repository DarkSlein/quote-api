from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
import traceback
from datetime import datetime, timezone

async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Кастомный обработчик ошибок валидации"""
    
    error_response = {
        "detail": [
            {
                "loc": err["loc"],
                "msg": err["msg"],
                "type": err["type"]
            } for err in exc.errors()
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "method": request.method,
    }
    
    # Добавляем тело запроса для отладки
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                error_response["body_preview"] = body[:1000].decode('utf-8', errors='ignore')
        except:
            error_response["body_error"] = "Could not read request body"
    
    # Добавляем stack trace в режиме отладки
    if hasattr(request.app, 'debug') and request.app.debug:
        error_response["debug"] = {
            "traceback": traceback.format_exc().split('\n'),
        }
    
    return JSONResponse(
        status_code=422,
        content=error_response
    )