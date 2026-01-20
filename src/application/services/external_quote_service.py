import aiohttp
from typing import List, Optional
from asyncio_throttle import Throttler

from domain.entities import Quote, Author
from domain.value_objects import QuoteText, Language, QuoteSource


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
                "page": "Заглавная_страница",
                "format": "json",
                "prop": "text"
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Здесь должна быть логика парсинга HTML
                        # Для примера возвращаем пустой список
                        return []
            except Exception as e:
                # Логируем ошибку и возвращаем пустой список
                return []

    async def _fetch_from_forismatic(self) -> List[Quote]:
        """Получение цитат с Forismatic API"""
        async with self.throttler:
            url = "http://api.forismatic.com/api/1.0/"
            params = {
                "method": "getQuote",
                "format": "json",
                "lang": "ru"
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote_text = data.get("quoteText", "")
                        author_name = data.get("quoteAuthor", "")
                        
                        if quote_text and author_name:
                            author = Author(name=author_name)
                            quote = Quote(
                                text=QuoteText(quote_text),
                                author=author,
                                language=Language("ru"),
                                source="forismatic.com"
                            )
                            return [quote]
            except Exception as e:
                return []
        
        return []