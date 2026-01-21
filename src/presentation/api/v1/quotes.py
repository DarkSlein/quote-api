from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field

from src.domain.entities import Quote, QuoteId
from src.application.use_cases.quotes import (
    GetQuoteUseCase,
    GetRandomQuoteUseCase,
    SearchQuotesUseCase,
    CreateQuoteUseCase,
    RateQuoteUseCase
)
from src.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from src.presentation.api.dependencies import get_uow

router = APIRouter(prefix="/quotes", tags=["quotes"])


# Pydantic схемы
class QuoteResponse(BaseModel):
    id: UUID
    text: str
    author: Optional[str] = None
    source: Optional[str] = None
    language: str
    rating: int
    created_at: str
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_domain(cls, quote: Quote) -> "QuoteResponse":
        return cls(
            id=quote.id.value,
            text=str(quote.text),
            author=quote.author.name if quote.author else None,
            source=quote.source,
            language=str(quote.language),
            rating=quote.rating.value,
            created_at=quote.created_at.isoformat()
        )


class CreateQuoteRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=2000)
    author: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    era: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=500)
    language: str = Field("ru", pattern="^[a-z]{2}$")


class QuoteListResponse(BaseModel):
    items: list[QuoteResponse]
    total: int
    page: int
    total_pages: int


@router.get("/random", response_model=list[QuoteResponse])
async def get_random_quote(
    category: Optional[str] = Query(None),
    era: Optional[str] = Query(None),
    min_rating: int = Query(0, ge=0),
    limit: int = Query(1, ge=1, le=10),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow)
):
    """Получить случайную цитату"""
    use_case = GetRandomQuoteUseCase(uow)
    quotes = await use_case.execute(category, era, min_rating, limit)
    return [QuoteResponse.from_domain(q) for q in quotes]


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: UUID,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow)
):
    """Получить цитату по ID"""
    use_case = GetQuoteUseCase(uow)
    try:
        quote = await use_case.execute(QuoteId(quote_id))
        return QuoteResponse.from_domain(quote)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/", response_model=QuoteListResponse)
async def search_quotes(
    query: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    era: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("rating", pattern="^(rating|created_at)$"),
    sort_desc: bool = Query(True),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow)
):
    """Поиск цитат с фильтрацией и пагинацией"""
    use_case = SearchQuotesUseCase(uow)
    quotes, total, total_pages = await use_case.execute(
        query=query,
        author=author,
        category=category,
        era=era,
        language=language,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc
    )
    
    return QuoteListResponse(
        items=[QuoteResponse.from_domain(q) for q in quotes],
        total=total,
        page=page,
        total_pages=total_pages
    )


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    request: CreateQuoteRequest,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow)
):
    """Создать новую цитату"""
    use_case = CreateQuoteUseCase(uow)
    try:
        quote = await use_case.execute(
            text=request.text,
            author_name=request.author,
            category_name=request.category,
            era_name=request.era,
            source=request.source,
            language=request.language
        )
        return QuoteResponse.from_domain(quote)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{quote_id}/rate", response_model=QuoteResponse)
async def rate_quote(
    quote_id: UUID,
    increment: int = Query(1, ge=-10, le=10),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow)
):
    """Оценить цитату"""
    use_case = RateQuoteUseCase(uow)
    try:
        quote = await use_case.execute(QuoteId(quote_id), increment)
        return QuoteResponse.from_domain(quote)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )