"""Shared exceptions and exit codes for audit scripts."""

from __future__ import annotations

from dataclasses import dataclass


class ExitCodes:
    """Standardized process exit codes for audit tools."""

    OK = 0
    USAGE_ERROR = 2
    AUTH_ERROR = 10
    VALIDATION_ERROR = 11
    DEPENDENCY_ERROR = 12
    COLLECTION_ERROR = 20
    PARSE_ERROR = 21
    OUTPUT_ERROR = 22
    PARTIAL_SUCCESS = 30
    UNKNOWN_ERROR = 99


@dataclass
class ToolError(Exception):
    """Base exception type for standardized tool failures."""

    message: str
    exit_code: int = ExitCodes.UNKNOWN_ERROR
    context: dict | None = None

    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "exit_code": self.exit_code,
            "context": self.context or {},
        }


class UsageError(ToolError):
    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message=message, exit_code=ExitCodes.USAGE_ERROR, context=context)


class AuthError(ToolError):
    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message=message, exit_code=ExitCodes.AUTH_ERROR, context=context)


class ValidationError(ToolError):
    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message=message, exit_code=ExitCodes.VALIDATION_ERROR, context=context)


class OutputError(ToolError):
    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message=message, exit_code=ExitCodes.OUTPUT_ERROR, context=context)
