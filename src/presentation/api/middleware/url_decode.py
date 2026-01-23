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
                
                # Обновляем scope без использования raw_path
                scope = dict(request.scope)
                # Обновляем только необходимые поля
                if "query_string" in scope:
                    scope["query_string"] = url.query.encode()
                
                # Обновляем path, если он изменился (редкий случай)
                if scope.get("path") != url.path:
                    scope["path"] = url.path
                
                # Создаем новый Request
                request = Request(scope, request.receive)
        
        return await call_next(request)