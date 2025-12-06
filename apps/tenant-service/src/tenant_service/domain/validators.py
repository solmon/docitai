"""Consolidated validators for domain entities.

This module provides centralized validation functions used across domain services.
All business rule validation should be defined here to ensure consistency and avoid
duplication across services.
"""

import re
from typing import Any, Optional
from uuid import UUID

from tenant_service.domain.enums.subscription_plan import SubscriptionPlan
from tenant_service.domain.enums.retention_types import (
    RetentionUnit,
    RetentionActionType,
)
from tenant_service.exceptions import ValidationError


# Email validation regex pattern (RFC 5322 simplified)
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Tenant name pattern (alphanumeric, hyphens, underscores)
TENANT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,62}[a-zA-Z0-9]$")

# Folder name pattern (no path separators)
FOLDER_NAME_PATTERN = re.compile(r"^[^/\\:*?\"<>|]+$")

# UUID pattern for validation
UUID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def validate_email(email: Optional[str], field_name: str = "email") -> None:
    """
    Validate email format.

    Args:
        email: Email address to validate (None is valid)
        field_name: Field name for error messages

    Raises:
        ValidationError: If email format is invalid
    """
    if email is None:
        return

    if not EMAIL_PATTERN.match(email):
        raise ValidationError(
            f"Invalid {field_name} format",
            details={field_name: email, "pattern": "user@domain.tld"},
        )


def validate_subscription_plan(plan: str) -> SubscriptionPlan:
    """
    Validate and normalize subscription plan.

    Args:
        plan: Subscription plan string

    Returns:
        Validated SubscriptionPlan enum value

    Raises:
        ValidationError: If plan is invalid
    """
    try:
        return SubscriptionPlan(plan.lower())
    except ValueError:
        valid_plans = [p.value for p in SubscriptionPlan]
        raise ValidationError(
            f"Invalid subscription plan: {plan}",
            details={"provided": plan, "valid_plans": valid_plans},
        )


def validate_tenant_name(name: str) -> str:
    """
    Validate tenant organization name.

    Requirements:
    - 4-64 characters
    - Starts and ends with alphanumeric
    - Contains only alphanumeric, hyphens, underscores

    Args:
        name: Tenant name to validate

    Returns:
        Validated tenant name (normalized)

    Raises:
        ValidationError: If name is invalid
    """
    if not name or len(name) < 4:
        raise ValidationError(
            "Tenant name must be at least 4 characters",
            details={"name": name, "min_length": 4},
        )

    if len(name) > 64:
        raise ValidationError(
            "Tenant name must be at most 64 characters",
            details={"name": name, "max_length": 64},
        )

    if not TENANT_NAME_PATTERN.match(name):
        raise ValidationError(
            "Tenant name must start and end with alphanumeric, contain only letters, numbers, hyphens, and underscores",
            details={"name": name},
        )

    return name


def validate_folder_name(name: str) -> str:
    """
    Validate folder name (no path separators or invalid characters).

    Args:
        name: Folder name to validate

    Returns:
        Validated folder name

    Raises:
        ValidationError: If name contains invalid characters
    """
    if not name or len(name) < 1:
        raise ValidationError(
            "Folder name cannot be empty",
            details={"name": name},
        )

    if len(name) > 255:
        raise ValidationError(
            "Folder name must be at most 255 characters",
            details={"name": name, "max_length": 255},
        )

    if not FOLDER_NAME_PATTERN.match(name):
        raise ValidationError(
            'Folder name cannot contain: / \\ : * ? " < > |',
            details={"name": name},
        )

    return name.strip()


def validate_folder_path(path: str) -> str:
    """
    Validate folder path format.

    Args:
        path: Folder path to validate

    Returns:
        Validated and normalized path

    Raises:
        ValidationError: If path format is invalid
    """
    if not path or not path.startswith("/"):
        raise ValidationError(
            "Folder path must start with /",
            details={"path": path},
        )

    # Normalize double slashes
    normalized = re.sub(r"/+", "/", path)

    # Check for invalid segments
    segments = normalized.strip("/").split("/")
    for segment in segments:
        if segment and not FOLDER_NAME_PATTERN.match(segment):
            raise ValidationError(
                f"Invalid path segment: {segment}",
                details={"path": path, "invalid_segment": segment},
            )

    return normalized


def validate_uuid(value: Any, field_name: str = "id") -> UUID:
    """
    Validate and convert UUID.

    Args:
        value: Value to validate as UUID
        field_name: Field name for error messages

    Returns:
        UUID object

    Raises:
        ValidationError: If value is not a valid UUID
    """
    if isinstance(value, UUID):
        return value

    if isinstance(value, str):
        if UUID_PATTERN.match(value):
            return UUID(value)

    raise ValidationError(
        f"Invalid {field_name}: must be a valid UUID",
        details={field_name: str(value)},
    )


def validate_retention_period(
    period: int,
    unit: RetentionUnit,
    min_days: int = 1,
    max_days: int = 36500,  # ~100 years
) -> int:
    """
    Validate retention period in days.

    Args:
        period: Retention period value
        unit: Retention time unit
        min_days: Minimum allowed days
        max_days: Maximum allowed days

    Returns:
        Period in days

    Raises:
        ValidationError: If period is out of bounds
    """
    # Convert to days based on unit
    if unit == RetentionUnit.DAYS:
        days = period
    elif unit == RetentionUnit.MONTHS:
        days = period * 30
    elif unit == RetentionUnit.YEARS:
        days = period * 365
    else:
        raise ValidationError(
            f"Invalid retention unit: {unit}",
            details={"unit": unit, "valid_units": [u.value for u in RetentionUnit]},
        )

    if days < min_days:
        raise ValidationError(
            f"Retention period must be at least {min_days} day(s)",
            details={"period": period, "unit": unit.value, "min_days": min_days},
        )

    if days > max_days:
        raise ValidationError(
            f"Retention period cannot exceed {max_days} days (~{max_days // 365} years)",
            details={"period": period, "unit": unit.value, "max_days": max_days},
        )

    return days


def validate_pagination(
    skip: int = 0,
    limit: int = 100,
    max_limit: int = 1000,
) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        max_limit: Maximum allowed limit

    Returns:
        Tuple of (skip, limit) validated values

    Raises:
        ValidationError: If parameters are invalid
    """
    if skip < 0:
        raise ValidationError(
            "Skip must be non-negative",
            details={"skip": skip},
        )

    if limit < 1:
        raise ValidationError(
            "Limit must be at least 1",
            details={"limit": limit},
        )

    if limit > max_limit:
        raise ValidationError(
            f"Limit cannot exceed {max_limit}",
            details={"limit": limit, "max_limit": max_limit},
        )

    return skip, limit


def validate_description(
    description: Optional[str],
    max_length: int = 1000,
    field_name: str = "description",
) -> Optional[str]:
    """
    Validate optional description field.

    Args:
        description: Description text (may be None)
        max_length: Maximum allowed length
        field_name: Field name for error messages

    Returns:
        Validated description or None

    Raises:
        ValidationError: If description exceeds max length
    """
    if description is None:
        return None

    if len(description) > max_length:
        raise ValidationError(
            f"{field_name} cannot exceed {max_length} characters",
            details={field_name: description[:50] + "...", "max_length": max_length},
        )

    return description.strip() if description else None


def validate_storage_provider(provider: str) -> str:
    """
    Validate storage provider type.

    Args:
        provider: Storage provider identifier

    Returns:
        Validated provider string

    Raises:
        ValidationError: If provider is not supported
    """
    valid_providers = ["s3", "azure_blob", "gcs", "local"]
    provider_lower = provider.lower()

    if provider_lower not in valid_providers:
        raise ValidationError(
            f"Unsupported storage provider: {provider}",
            details={"provider": provider, "valid_providers": valid_providers},
        )

    return provider_lower


def validate_retention_action(action: str) -> RetentionActionType:
    """
    Validate retention action type.

    Args:
        action: Action type string

    Returns:
        Validated RetentionActionType enum

    Raises:
        ValidationError: If action is invalid
    """
    try:
        return RetentionActionType(action.lower())
    except ValueError:
        valid_actions = [a.value for a in RetentionActionType]
        raise ValidationError(
            f"Invalid retention action: {action}",
            details={"action": action, "valid_actions": valid_actions},
        )
