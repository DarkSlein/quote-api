class DomainException(Exception):
    """Базовое исключение доменного слоя"""
    pass


class QuoteNotFoundException(DomainException):
    """Цитата не найдена"""
    pass


class AuthorNotFoundException(DomainException):
    """Автор не найден"""
    pass


class InvalidQuoteException(DomainException):
    """Некорректная цитата"""
    pass


class QuoteAlreadyExistsException(DomainException):
    """Цитата уже существует"""
    pass


class RateLimitExceededException(DomainException):
    """Превышен лимит запросов"""
    pass