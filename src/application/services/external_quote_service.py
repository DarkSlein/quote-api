import aiohttp
from typing import List, Optional
from asyncio_throttle import Throttler

from src.domain.entities import Quote, Author
from src.domain.value_objects import QuoteText, Language, QuoteSource


class ExternalQuoteService:
    def __init__(self):
        self.throttler = Throttler(rate_limit=10, period=1)  # 10 запросов в секунду
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_quotes(self, source: QuoteSource) -> List[Quote]:
        """Получение цитат из внешних источников"""
        if source == QuoteSource.WIKIQUOTE:
            return await self._fetch_from_wikiquote()
        elif source == QuoteSource.FORISMATIC:
            return await self._fetch_from_forismatic()
        else:
            return []

    async def _fetch_from_wikiquote(self) -> List[Quote]:
        """Парсинг цитат с WikiQuote"""
        async with self.throttler:
            url = "https://ru.wikiquote.org/w/api.php"
            params = {
                "action": "parse",
                "page": "Афоризм",
                "format": "json",
                "prop": "text"
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Возвращаем пустой список, так как парсинг WikiQuote сложный
                        # В будущем можно реализовать полноценный парсинг
                        return []
                    else:
                        return []
            except Exception as e:
                # Логируем ошибку и возвращаем пустой список
                return []

    async def _fetch_from_forismatic(self) -> List[Quote]:
        """Получение цитат с Forismatic API"""
        quotes = []
        
        # Делаем несколько запросов для получения нескольких цитат
        for _ in range(3):  # Получаем 3 цитаты за раз
            async with self.throttler:
                url = "http://api.forismatic.com/api/1.0/"
                params = {
                    "method": "getQuote",
                    "format": "json",
                    "lang": "ru",
                    "key": "457653"  # Пример ключа
                }
                
                try:
                    async with self.session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            quote_text = data.get("quoteText", "").strip()
                            author_name = data.get("quoteAuthor", "").strip()
                            
                            if quote_text and author_name:
                                author = Author(name=author_name)
                                quote = Quote(
                                    text=QuoteText(quote_text),
                                    author=author,
                                    language=Language("ru"),
                                    source="forismatic.com"
                                )
                                quotes.append(quote)
                except Exception as e:
                    # Продолжаем попытки для других цитат
                    continue
        
        return quotes


# Альтернативно, отключите обновление из wikiquote в настройках:
# В src/shared/config.py добавьте:
# UPDATE_SOURCES = os.getenv("UPDATE_SOURCES", "forismatic")  # Только forismatic