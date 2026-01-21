from dataclasses import dataclass
from enum import Enum

from src.domain.exceptions import DomainException


@dataclass(frozen=True)
class QuoteText:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise DomainException("Quote text cannot be empty")
        if len(self.value) > 2000:
            raise DomainException("Quote text is too long")
        if len(self.value.split()) < 3:
            raise DomainException("Quote text is too short")

    def __str__(self) -> str:
        return self.value

    @property
    def word_count(self) -> int:
        return len(self.value.split())

    @property
    def is_question(self) -> bool:
        return self.value.strip().endswith("?")


@dataclass(frozen=True)
class Language:
    _code: str

    def __post_init__(self) -> None:
        if len(self._code) != 2:
            raise DomainException("Language code must be 2 characters")
        if not self._code.islower():
            raise DomainException("Language code must be lowercase")

    @property
    def code(self) -> str:
        """Публичный геттер для кода языка."""
        return self._code


@dataclass(frozen=True)
class Rating:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise DomainException("Rating cannot be negative")

    @classmethod
    def zero(cls) -> "Rating":
        return Rating(0)

    def increment(self) -> "Rating":
        return Rating(self.value + 1)

    def decrement(self) -> "Rating":
        return Rating(max(0, self.value - 1))


class QuoteSource(Enum):
    WIKIQUOTE = "wikiquote"
    FORISMATIC = "forismatic"
    MANUAL = "manual"
    IMPORT = "import"


@dataclass(frozen=True)
class UpdateResult:
    source: QuoteSource
    added: int
    updated: int
    errors: int

    @property
    def total(self) -> int:
        return self.added + self.updated

    @property
    def success_rate(self) -> float:
        total = self.total + self.errors
        return (self.total / total) * 100 if total > 0 else 0.0