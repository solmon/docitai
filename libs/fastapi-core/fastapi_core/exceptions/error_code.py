from enum import Enum


class ErrorCode(str, Enum):
    RESOURCE_NOT_FOUND = "resource_not_found"
    PATH_NOT_FOUND = "path_not_found"
    DATABASE_CONNECTION = "database_connection"
    DATABASE_API_OPERATION = "database_api_operation"
    REQUEST_VALIDATION = "request_validation"
    UNCLASSIFIED = "unclassified"
