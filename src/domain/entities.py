from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from src.domain.value_objects import QuoteText, Language, Rating
from src.domain.exceptions import DomainException


@dataclass(frozen=True, eq=True)
class QuoteId:
    value: UUID

    @classmethod
    def generate(cls) -> "QuoteId":
        return QuoteId(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Author:
    name: str
    id: UUID = field(default_factory=uuid4)
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    bio: Optional[str] = None
    created_at: datetime = \
      field(default_factory=lambda: datetime.now(timezone.utc))

    def is_alive(self) -> bool:
        return self.death_year is None

    def validate(self) -> None:
        if not self.name.strip():
            raise DomainException("Author name cannot be empty")
        if self.birth_year and self.death_year:
            if self.death_year < self.birth_year:
                raise DomainException("Death year cannot be before birth year")


@dataclass
class Category:
    name: str
    id: UUID = field(default_factory=uuid4)
    description: Optional[str] = None

    def validate(self) -> None:
        if not self.name.strip():
            raise DomainException("Category name cannot be empty")


@dataclass
class Era:
    name: str
    id: UUID = field(default_factory=uuid4)
    start_year: Optional[int] = None
    end_year: Optional[int] = None

    def validate(self) -> None:
        if not self.name.strip():
            raise DomainException("Era name cannot be empty")
        if self.start_year and self.end_year:
            if self.end_year < self.start_year:
                raise DomainException("End year cannot be before start year")


@dataclass
class Quote:
    text: QuoteText
    author: Optional[Author] = None
    category: Optional[Category] = None
    era: Optional[Era] = None
    source: Optional[str] = None
    id: QuoteId = field(default_factory=QuoteId.generate)
    language: Language = field(default_factory=lambda: Language("ru"))
    rating: Rating = field(default_factory=Rating.zero)
    created_at: datetime = field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.validate()

    def rate(self, increment: int = 1) -> None:
        self.rating = Rating(self.rating.value + increment)
        self.updated_at = datetime.now(timezone.utc)

    def update_text(self, new_text: QuoteText) -> None:
        self.text = new_text
        self.updated_at = datetime.now(timezone.utc)
