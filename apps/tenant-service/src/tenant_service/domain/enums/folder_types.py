"""Folder enums and types."""

from enum import Enum


class FolderOperation(str, Enum):
    """Types of folder operations for audit trail."""

    CREATE = "create"
    MOVE = "move"
    DELETE = "delete"
    ARCHIVE = "archive"
    RESTORE = "restore"


class FolderStatus(str, Enum):
    """Status of a folder."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
