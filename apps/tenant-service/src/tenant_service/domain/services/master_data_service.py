"""Master Data Service - Business Logic Layer

Implements business logic for document categories and types.
"""

from typing import Any, Optional
from uuid import UUID

from sqlmodel import Session

from tenant_service.domain.value_objects.custom_attribute import (
    AttributeValidationError,
    CustomAttribute,
)
from tenant_service.infrastructure.models.document_category import DocumentCategory
from tenant_service.infrastructure.models.document_type import DocumentType
from tenant_service.infrastructure.models.master_data_version import MasterDataVersion
from tenant_service.infrastructure.repositories.category_repository import (
    DocumentCategoryRepository,
)
from tenant_service.infrastructure.repositories.document_type_repository import (
    DocumentTypeRepository,
)
from tenant_service.infrastructure.repositories.master_data_version_repository import (
    MasterDataVersionRepository,
)


class MasterDataService:
    """Service for master data management"""

    def __init__(self, db: Session):
        self.db = db
        self.category_repo = DocumentCategoryRepository(db)
        self.type_repo = DocumentTypeRepository(db)
        self.version_repo = MasterDataVersionRepository(db)

    # ============= Category Operations =============

    async def create_category(
        self,
        tenant_id: UUID,
        name: str,
        description: Optional[str] = None,
        color_code: Optional[str] = None,
        icon: Optional[str] = None,
        parent_category_id: Optional[UUID] = None,
        sort_order: int = 0,
    ) -> DocumentCategory:
        """Create a new document category
        
        Args:
            tenant_id: Tenant ID
            name: Category name
            description: Optional description
            color_code: Optional hex color
            icon: Optional icon name
            parent_category_id: Optional parent category (hierarchy)
            sort_order: Sort order for UI
            
        Returns:
            Created category
            
        Raises:
            ValueError: If category name exists or parent doesn't exist
        """
        # Check uniqueness
        if await self.category_repo.exists_by_name(name, tenant_id):
            raise ValueError(f"Category '{name}' already exists in tenant")

        # Validate parent exists if provided
        if parent_category_id:
            parent = await self.category_repo.get_by_id(parent_category_id, tenant_id)
            if not parent:
                raise ValueError("Parent category not found")

            # Prevent circular references (can't be own parent)
            if parent_category_id == parent_category_id:
                raise ValueError("Cannot set category as its own parent")

        category = DocumentCategory(
            tenant_id=tenant_id,
            name=name,
            description=description,
            color_code=color_code,
            icon=icon,
            parent_category_id=parent_category_id,
            sort_order=sort_order,
            is_active=True,
        )

        return await self.category_repo.create(category)

    async def update_category(
        self,
        category_id: UUID,
        tenant_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color_code: Optional[str] = None,
        icon: Optional[str] = None,
        parent_category_id: Optional[UUID] = None,
        sort_order: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> DocumentCategory:
        """Update an existing category
        
        Args:
            category_id: Category ID
            tenant_id: Tenant ID
            name: New name (optional)
            description: New description (optional)
            color_code: New color (optional)
            icon: New icon (optional)
            parent_category_id: New parent (optional)
            sort_order: New sort order (optional)
            is_active: Active status (optional)
            
        Returns:
            Updated category
            
        Raises:
            ValueError: If category not found or update invalid
        """
        category = await self.category_repo.get_by_id(category_id, tenant_id)
        if not category:
            raise ValueError("Category not found")

        # Check new name uniqueness if changing
        if name and name != category.name:
            if await self.category_repo.exists_by_name(name, tenant_id):
                raise ValueError(f"Category '{name}' already exists in tenant")

        # Validate new parent
        if parent_category_id is not None and parent_category_id != category.parent_category_id:
            if parent_category_id:
                parent = await self.category_repo.get_by_id(parent_category_id, tenant_id)
                if not parent:
                    raise ValueError("Parent category not found")

                # Check for circular reference
                if parent_category_id == category_id:
                    raise ValueError("Cannot set category as its own parent")

                # Check if new parent is descendant
                descendants = await self.category_repo.get_descendants(category_id, tenant_id)
                if any(d.id == parent_category_id for d in descendants):
                    raise ValueError("Cannot set descendant as parent (circular reference)")

        # Update fields
        if name:
            category.name = name
        if description is not None:
            category.description = description
        if color_code is not None:
            category.color_code = color_code
        if icon is not None:
            category.icon = icon
        if parent_category_id is not None:
            category.parent_category_id = parent_category_id
        if sort_order is not None:
            category.sort_order = sort_order
        if is_active is not None:
            category.is_active = is_active

        return await self.category_repo.update(category)

    async def delete_category(self, category_id: UUID, tenant_id: UUID) -> bool:
        """Delete a category (soft delete)
        
        Args:
            category_id: Category ID
            tenant_id: Tenant ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            ValueError: If category has active document types
        """
        # Check for active document types in this category
        types_count = await self.type_repo.count_by_category(category_id, tenant_id)
        if types_count > 0:
            raise ValueError(
                f"Cannot delete category with {types_count} document types"
            )

        return await self.category_repo.soft_delete(category_id, tenant_id)

    async def restore_category(self, category_id: UUID, tenant_id: UUID) -> bool:
        """Restore a soft-deleted category
        
        Args:
            category_id: Category ID
            tenant_id: Tenant ID
            
        Returns:
            True if restored, False if not found
        """
        return await self.category_repo.restore(category_id, tenant_id)

    async def get_category_hierarchy(
        self, tenant_id: UUID
    ) -> dict[str, Any]:
        """Get complete category hierarchy as tree
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tree structure with categories
        """
        all_categories = await self.category_repo.get_category_tree(tenant_id)
        root_categories = [c for c in all_categories if c.parent_category_id is None]

        def build_tree(category):
            children = [
                build_tree(c)
                for c in all_categories
                if c.parent_category_id == category.id
            ]
            return {
                "id": str(category.id),
                "name": category.name,
                "description": category.description,
                "color_code": category.color_code,
                "icon": category.icon,
                "children": children,
            }

        return {
            "categories": [build_tree(c) for c in root_categories]
        }

    # ============= Document Type Operations =============

    async def create_document_type(
        self,
        tenant_id: UUID,
        category_id: UUID,
        name: str,
        description: Optional[str] = None,
        file_extensions: Optional[list[str]] = None,
        max_file_size: int = 10485760,  # 10MB
        retention_days: Optional[int] = None,
        custom_attributes: Optional[list[dict[str, Any]]] = None,
    ) -> DocumentType:
        """Create a new document type
        
        Args:
            tenant_id: Tenant ID
            category_id: Category ID
            name: Type name
            description: Optional description
            file_extensions: Allowed file extensions
            max_file_size: Max file size in bytes
            retention_days: Retention period (days)
            custom_attributes: Custom attribute definitions
            
        Returns:
            Created document type
            
        Raises:
            ValueError: If validation fails
        """
        # Check uniqueness
        if await self.type_repo.exists_by_name(name, tenant_id):
            raise ValueError(f"Document type '{name}' already exists")

        # Validate category exists
        category = await self.category_repo.get_by_id(category_id, tenant_id)
        if not category:
            raise ValueError("Category not found")

        # Validate custom attributes
        if custom_attributes:
            validated_attrs = await self._validate_attribute_schema(custom_attributes)
        else:
            validated_attrs = []

        doc_type = DocumentType(
            tenant_id=tenant_id,
            name=name,
            description=description,
            category_id=category_id,
            file_extensions=file_extensions or [],
            max_file_size=max_file_size,
            retention_days=retention_days,
            custom_attributes=validated_attrs,
            is_active=True,
        )

        return await self.type_repo.create(doc_type)

    async def update_document_type(
        self,
        type_id: UUID,
        tenant_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category_id: Optional[UUID] = None,
        file_extensions: Optional[list[str]] = None,
        max_file_size: Optional[int] = None,
        retention_days: Optional[int] = None,
        custom_attributes: Optional[list[dict[str, Any]]] = None,
        is_active: Optional[bool] = None,
    ) -> DocumentType:
        """Update a document type
        
        Args:
            type_id: Type ID
            tenant_id: Tenant ID
            name: New name (optional)
            description: New description (optional)
            category_id: New category (optional)
            file_extensions: New extensions (optional)
            max_file_size: New max size (optional)
            retention_days: New retention (optional)
            custom_attributes: New attributes (optional)
            is_active: Active status (optional)
            
        Returns:
            Updated document type
            
        Raises:
            ValueError: If type not found or update invalid
        """
        doc_type = await self.type_repo.get_by_id(type_id, tenant_id)
        if not doc_type:
            raise ValueError("Document type not found")

        # Check name uniqueness if changing
        if name and name != doc_type.name:
            if await self.type_repo.exists_by_name(name, tenant_id):
                raise ValueError(f"Document type '{name}' already exists")

        # Validate category if changing
        if category_id and category_id != doc_type.category_id:
            category = await self.category_repo.get_by_id(category_id, tenant_id)
            if not category:
                raise ValueError("Category not found")

        # Validate custom attributes if changing
        if custom_attributes is not None:
            validated_attrs = await self._validate_attribute_schema(custom_attributes)
            doc_type.custom_attributes = validated_attrs

        # Update fields
        if name:
            doc_type.name = name
        if description is not None:
            doc_type.description = description
        if category_id:
            doc_type.category_id = category_id
        if file_extensions is not None:
            doc_type.file_extensions = file_extensions
        if max_file_size is not None:
            doc_type.max_file_size = max_file_size
        if retention_days is not None:
            doc_type.retention_days = retention_days
        if is_active is not None:
            doc_type.is_active = is_active

        return await self.type_repo.update(doc_type)

    async def delete_document_type(self, type_id: UUID, tenant_id: UUID) -> bool:
        """Delete a document type (soft delete)
        
        Args:
            type_id: Type ID
            tenant_id: Tenant ID
            
        Returns:
            True if deleted, False if not found
        """
        return await self.type_repo.soft_delete(type_id, tenant_id)

    async def restore_document_type(self, type_id: UUID, tenant_id: UUID) -> bool:
        """Restore a soft-deleted document type
        
        Args:
            type_id: Type ID
            tenant_id: Tenant ID
            
        Returns:
            True if restored, False if not found
        """
        return await self.type_repo.restore(type_id, tenant_id)

    # ============= Attribute Validation =============

    async def _validate_attribute_schema(
        self, attributes_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Validate custom attributes schema
        
        Args:
            attributes_data: List of attribute dictionaries
            
        Returns:
            Validated and normalized attributes
            
        Raises:
            ValueError: If schema is invalid
        """
        if len(attributes_data) > 50:
            raise ValueError("Maximum 50 custom attributes allowed")

        attributes = []
        seen_names = set()

        for attr_data in attributes_data:
            try:
                attr = CustomAttribute.from_dict(attr_data)

                # Check uniqueness
                if attr.name in seen_names:
                    raise ValueError(f"Duplicate attribute name: {attr.name}")
                seen_names.add(attr.name)

                attributes.append(attr.to_dict())
            except ValueError as e:
                raise ValueError(f"Invalid attribute: {e}")

        return attributes

    async def validate_document_data(
        self, doc_type: DocumentType, data: dict[str, Any]
    ) -> list[str]:
        """Validate document data against type schema
        
        Args:
            doc_type: Document type
            data: Document data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for attr_dict in doc_type.custom_attributes:
            attr = CustomAttribute.from_dict(attr_dict)
            value = data.get(attr.name)

            is_valid, error_msg = attr.validate_value(value)
            if not is_valid:
                errors.append(error_msg)

        return errors

    async def get_attribute_constraints(
        self, attribute_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """Get JSON schema constraints for attribute
        
        Args:
            attribute_dict: Attribute dictionary
            
        Returns:
            JSON schema representation
        """
        attr = CustomAttribute.from_dict(attribute_dict)

        schema = {
            "type": attr.attribute_type.value,
            "required": attr.required,
            "description": attr.description,
        }

        if attr.default_value is not None:
            schema["default"] = attr.default_value

        if attr.validation_rules:
            schema["constraints"] = attr.validation_rules

        if attr.enum_values:
            schema["enum"] = attr.enum_values

        return schema

    # ============= Versioning Operations =============

    async def record_version(
        self,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
        action: str,
        tenant_id: UUID,
        new_values: dict[str, Any],
        previous_values: Optional[dict[str, Any]] = None,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None,
    ) -> MasterDataVersion:
        """Record a version change for audit trail
        
        Args:
            entity_type: Type of entity (category/type)
            entity_id: Entity ID
            entity_name: Entity name
            action: Action (create/update/delete/restore)
            tenant_id: Tenant ID
            new_values: New field values
            previous_values: Previous values (for updates)
            changed_by: User who made change
            change_reason: Reason for change
            
        Returns:
            Recorded version
        """
        # Calculate changed fields
        changed_fields = []
        if previous_values and new_values:
            for key in new_values:
                if key not in previous_values or previous_values[key] != new_values[key]:
                    changed_fields.append(key)

        version = MasterDataVersion(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            action=action,
            previous_values=previous_values,
            new_values=new_values,
            changed_fields=changed_fields,
            changed_by=changed_by,
            change_reason=change_reason,
        )

        return await self.version_repo.record_version(version)

    async def get_version_history(
        self, entity_id: UUID, tenant_id: UUID
    ) -> list[MasterDataVersion]:
        """Get complete version history for entity
        
        Args:
            entity_id: Entity ID
            tenant_id: Tenant ID
            
        Returns:
            List of all versions
        """
        return await self.version_repo.get_version_history(entity_id, tenant_id)

    async def get_version(
        self, entity_id: UUID, version_number: int, tenant_id: UUID
    ) -> Optional[MasterDataVersion]:
        """Get specific version
        
        Args:
            entity_id: Entity ID
            version_number: Version number
            tenant_id: Tenant ID
            
        Returns:
            Specific version or None
        """
        return await self.version_repo.get_version(entity_id, version_number, tenant_id)

    async def rollback_to_version(
        self, entity_id: UUID, version_number: int, tenant_id: UUID, user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Rollback entity to previous version
        
        Args:
            entity_id: Entity ID
            version_number: Version to restore to
            tenant_id: Tenant ID
            user_id: User performing rollback
            
        Returns:
            Rolled back entity as dict
            
        Raises:
            ValueError: If version not found
        """
        # Get target version
        version = await self.version_repo.get_version(entity_id, version_number, tenant_id)
        if not version:
            raise ValueError(f"Version {version_number} not found")

        # Record rollback as new version
        await self.record_version(
            entity_type=version.entity_type,
            entity_id=entity_id,
            entity_name=version.entity_name,
            action="rollback",
            tenant_id=tenant_id,
            new_values=version.new_values,
            previous_values=version.previous_values,
            changed_by=user_id,
            change_reason=f"Rollback to version {version_number}",
        )

        return version.new_values
