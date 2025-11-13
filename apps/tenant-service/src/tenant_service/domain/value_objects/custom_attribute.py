"""Custom Attribute Value Object - Immutable attribute definition

Represents a custom attribute template for document types.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import Field, field_validator
from sqlmodel import SQLModel


class AttributeType(str, Enum):
    """Supported custom attribute types"""

    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ENUM = "enum"
    JSON = "json"


class CustomAttribute(SQLModel):
    """Immutable custom attribute definition
    
    Value object representing a custom attribute that can be attached
    to document types for capturing additional metadata.
    """

    name: str = Field(
        ...,
        description="Attribute name (identifier)",
        min_length=1,
        max_length=100,
    )
    attribute_type: AttributeType = Field(
        ...,
        description="Attribute data type",
    )
    required: bool = Field(
        default=False,
        description="Attribute is required when document created",
    )
    default_value: Optional[Any] = Field(
        None,
        description="Default value if not provided",
    )
    validation_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific validation rules",
    )
    enum_values: Optional[list[Any]] = Field(
        None,
        description="Valid enum values (for enum type)",
    )
    description: Optional[str] = Field(
        None,
        description="Attribute description for UI",
        max_length=500,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate attribute name is valid identifier"""
        if not v.isidentifier():
            raise ValueError("Attribute name must be valid Python identifier")
        return v

    @field_validator("enum_values", mode="before")
    @classmethod
    def validate_enum_values(cls, v: Optional[list[Any]], info) -> Optional[list[Any]]:
        """Validate enum values if present"""
        if info.data.get("attribute_type") == AttributeType.ENUM:
            if not v or len(v) == 0:
                raise ValueError("enum_values required for enum type")
            if len(v) > 1000:
                raise ValueError("Maximum 1000 enum values allowed")
        return v

    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate a value against this attribute definition
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required
        if self.required and value is None:
            return False, f"{self.name} is required"

        # None is valid if not required
        if value is None:
            return True, None

        # Type-specific validation
        if self.attribute_type == AttributeType.TEXT:
            if not isinstance(value, str):
                return False, f"{self.name} must be string"
            max_length = self.validation_rules.get("max_length", 10000)
            if len(value) > max_length:
                return False, f"{self.name} exceeds max length {max_length}"

        elif self.attribute_type == AttributeType.NUMBER:
            try:
                num = float(value) if not isinstance(value, (int, float)) else value
            except (ValueError, TypeError):
                return False, f"{self.name} must be numeric"
            
            min_val = self.validation_rules.get("min")
            max_val = self.validation_rules.get("max")
            if min_val is not None and num < min_val:
                return False, f"{self.name} must be >= {min_val}"
            if max_val is not None and num > max_val:
                return False, f"{self.name} must be <= {max_val}"

        elif self.attribute_type == AttributeType.BOOLEAN:
            if not isinstance(value, bool):
                return False, f"{self.name} must be boolean"

        elif self.attribute_type == AttributeType.DATE:
            if isinstance(value, str):
                try:
                    from datetime import datetime
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return False, f"{self.name} must be YYYY-MM-DD format"
            else:
                return False, f"{self.name} must be string (YYYY-MM-DD)"

        elif self.attribute_type == AttributeType.DATETIME:
            if isinstance(value, str):
                try:
                    from datetime import datetime
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    return False, f"{self.name} must be ISO 8601 format"
            else:
                return False, f"{self.name} must be string (ISO 8601)"

        elif self.attribute_type == AttributeType.ENUM:
            if self.enum_values and value not in self.enum_values:
                valid = ", ".join(str(v) for v in self.enum_values)
                return False, f"{self.name} must be one of: {valid}"

        elif self.attribute_type == AttributeType.JSON:
            if isinstance(value, dict):
                pass  # Valid JSON object
            elif isinstance(value, list):
                pass  # Valid JSON array
            else:
                return False, f"{self.name} must be JSON object or array"

        return True, None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "name": self.name,
            "attribute_type": self.attribute_type.value,
            "required": self.required,
            "default_value": self.default_value,
            "validation_rules": self.validation_rules,
            "enum_values": self.enum_values,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CustomAttribute":
        """Create from dictionary"""
        if isinstance(data.get("attribute_type"), str):
            data["attribute_type"] = AttributeType(data["attribute_type"])
        return cls(**data)

    def __hash__(self) -> int:
        """Value object equality by content"""
        return hash((self.name, self.attribute_type, self.required))

    def __eq__(self, other: Any) -> bool:
        """Compare custom attributes by name and type"""
        if not isinstance(other, CustomAttribute):
            return False
        return (
            self.name == other.name
            and self.attribute_type == other.attribute_type
            and self.required == other.required
        )


class AttributeValidationError(Exception):
    """Raised when attribute validation fails"""

    def __init__(self, attribute_name: str, message: str):
        self.attribute_name = attribute_name
        self.message = message
        super().__init__(f"{attribute_name}: {message}")
