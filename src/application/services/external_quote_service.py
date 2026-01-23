import asyncio
import aiohttp
from typing import List, Optional
from asyncio_throttle import Throttler
import random

from src.domain.entities import Quote, Author
from src.domain.value_objects import QuoteText, Language, QuoteSource


class ExternalQuoteService:
    def __init__(self):
        self.throttler = Throttler(rate_limit=2, period=1)  # 2 запроса в секунду (лимит forismatic)
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
            # Используем более подходящую страницу
            url = "https://ru.wikiquote.org/w/api.php"
            params = {
                "action": "parse",
                "page": "Цитаты_дня",
                "format": "json",
                "prop": "text"
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Пока возвращаем пустой список
                        return []
            except Exception:
                return []
        return []

    async def _fetch_from_forismatic(self) -> List[Quote]:
        """Получение цитат с Forismatic API"""
        import re
        
        quotes = []
        seen = set()
        
        for attempt in range(3):  # 3 попытки
            async with self.throttler:
                try:
                    url = "http://api.forismatic.com/api/1.0/"
                    params = {
                        "method": "getQuote",
                        "format": "json",
                        "lang": "ru",
                        "key": random.randint(1, 999999) # hash(f"attempt{attempt}") % 1000000
                    }
                    
                    async with self.session.get(url, params=params, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            quote_text = data.get("quoteText", "").strip()
                            author_name = data.get("quoteAuthor", "").strip()
                            
                            # Очищаем текст
                            quote_text = re.sub(r'\s+', ' ', quote_text).strip()
                            
                            if not quote_text:
                                continue
                            
                            if not author_name or author_name == "":
                                author_name = "Неизвестный автор"
                            
                            # Проверяем на дубликаты в рамках одной сессии
                            quote_key = f"{quote_text[:100]}|{author_name}"
                            if quote_key in seen:
                                continue
                            seen.add(quote_key)
                            
                            # Создаем автора с корректным временем
                            author = Author(name=author_name)
                            
                            # Создаем цитату
                            quote = Quote(
                                text=QuoteText(quote_text),
                                author=author,
                                language=Language("ru"),
                                source="forismatic.com"
                            )
                            quotes.append(quote)
                            
                except Exception:
                    continue
        
        return quotes