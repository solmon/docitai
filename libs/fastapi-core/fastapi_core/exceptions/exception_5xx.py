from http import HTTPStatus

from fastapi import HTTPException

from .error_code import ErrorCode


class DbConnectionException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail={"error": "Database is currently unreachable", "error_code": ErrorCode.DATABASE_CONNECTION},
        )
