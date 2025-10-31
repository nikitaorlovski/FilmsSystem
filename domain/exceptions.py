class DomainError(Exception):
    """Base class for all domain-level exceptions."""

    pass


class InvalidCredentialsError(DomainError):
    """Raised when credentials are invalid."""

    pass


class UserAlreadyExistsError(DomainError):
    """Raised when trying to create a user with existing email."""

    pass
