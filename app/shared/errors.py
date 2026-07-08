"""Shared error types for cross-layer communication.

These are plain error classes that any layer can raise or catch
without creating a dependency on a specific layer.
"""


class DomainError(Exception):
    """Base for errors originating in the domain layer."""


class RecognitionError(Exception):
    """Base for errors originating in the recognition layer."""


class InfrastructureError(Exception):
    """Base for infrastructure / I/O errors."""


class ValidationError(DomainError):
    """Input data fails business-rule validation."""
