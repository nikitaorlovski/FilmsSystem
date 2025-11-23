class DomainError(Exception):
    """Base class for all domain-level exceptions."""

    pass


class InvalidCredentialsError(DomainError):
    """Raised when credentials are invalid."""

    pass


class UserAlreadyExistsError(DomainError):
    """Raised when trying to create a user with existing email."""

    pass

class UserValidationError(DomainError):
    """Ошибка валидации данных пользователя"""
    pass

class FilmNotFound(DomainError):
    """Raised when film not founded."""

    pass


class HallNotFound(DomainError):
    """Raised when hall not founded."""

    pass

class HallValidationError(DomainError):
    """Ошибка валидации данных зала"""
    pass

class HallAlreadyExistsError(DomainError):
    """Зал с таким названием уже существует"""
    pass


class SessionConflictError(DomainError):
    """Hall already has another session in this time."""

    pass

class SessionNotFoundError(DomainError):
    """Сеанс не найден"""
    pass

class SessionHasActiveBookingsError(DomainError):
    """У сеанса есть активные бронирования"""
    pass

class FilmValidationError(DomainError):
    """Ошибка валидации данных фильма"""
    pass

class FilmAlreadyExistsError(DomainError):
    """Фильм с таким названием уже существует"""
    pass

class HallHasFutureSessionsError(DomainError):
    """Нельзя удалить зал с будущими сеансами"""
    pass