import urllib.parse
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class URLDecodeMiddleware(BaseHTTPMiddleware):
    """Middleware для декодирования URL параметров"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Получаем query параметры
        query_string = str(request.url.query)
        
        if query_string:
            # Декодируем плюсы и другие спецсимволы
            decoded_query = urllib.parse.unquote_plus(query_string)
            
            # Если есть изменения, создаем новый Request
            if decoded_query != query_string:
                # Создаем новый URL с декодированными параметрами
                url = request.url.replace(query=decoded_query)
                scope = dict(request.scope)
                scope["raw_path"] = url.raw_path
                scope["path"] = url.path
                scope["query_string"] = url.query.encode()
                
                # Создаем новый Request с декодированными параметрами
                request = Request(scope, request.receive)
        
        return await call_next(request)