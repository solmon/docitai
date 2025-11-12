from http import HTTPStatus

from fastapi import HTTPException

from .error_code import ErrorCode


class ResourceNotFoundException(HTTPException):
    def __init__(self, resource_name: str = "Resource"):
        super().__init__(
            status_code=HTTPStatus.NOT_FOUND,
            detail={"error": f"{resource_name} not found", "error_code": ErrorCode.RESOURCE_NOT_FOUND},
        )
