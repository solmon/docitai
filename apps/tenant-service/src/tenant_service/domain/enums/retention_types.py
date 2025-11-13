"""Retention policy enums and types."""

from enum import Enum


class ResourceType(str, Enum):
    """Types of resources subject to retention."""

    DOCUMENT = "document"
    FOLDER = "folder"
    ALL = "all"


class RetentionType(str, Enum):
    """Retention action types."""

    DELETE = "delete"
    ARCHIVE = "archive"


class AppliesTo(str, Enum):
    """Scope of retention policy application."""

    ALL = "all"
    SPECIFIC_CATEGORIES = "specific_categories"
    SPECIFIC_FOLDERS = "specific_folders"


class AuditActionType(str, Enum):
    """Types of compliance audit actions."""

    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_EXECUTED = "policy_executed"
    POLICY_DELETED = "policy_deleted"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_ARCHIVED = "document_archived"
    FOLDER_DELETED = "folder_deleted"
    COMPLIANCE_VERIFIED = "compliance_verified"


class ComplianceStatus(str, Enum):
    """Status of compliance actions."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
