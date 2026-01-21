from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
import traceback

async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Кастомный обработчик ошибок валидации"""
    debug = request.app.debug if hasattr(request.app, 'debug') else False
    
    error_response = {
        "detail": [
            {
                "loc": err["loc"],
                "msg": err["msg"],
                "type": err["type"]
            } for err in exc.errors()
        ],
        "body": exc.body if hasattr(exc, 'body') else None
    }
    
    # Добавляем stack trace в debug режиме
    if debug:
        error_response["debug"] = {
            "traceback": traceback.format_exc().split('\n'),
            "path": request.url.path,
            "method": request.method
        }
    
    return JSONResponse(
        status_code=422,
        content=error_response
    )