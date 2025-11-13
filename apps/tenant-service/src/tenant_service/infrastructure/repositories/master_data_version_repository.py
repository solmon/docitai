"""Master Data Versioning Repository - Immutable Audit Trail

Handles version history tracking for master data entities.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlmodel import Session

from tenant_service.infrastructure.models.master_data_version import MasterDataVersion


class MasterDataVersionRepository:
    """Repository for Master Data Version (audit trail) access"""

    def __init__(self, db: Session):
        self.db = db

    async def record_version(
        self,
        version: MasterDataVersion,
    ) -> MasterDataVersion:
        """Record a new version (append-only)
        
        Args:
            version: MasterDataVersion to record
            
        Returns:
            Recorded version with ID
        """
        # Calculate version number
        current_versions = await self.count_entity_versions(
            version.entity_id, version.tenant_id
        )
        version.version_number = current_versions + 1

        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def get_version(
        self,
        entity_id: UUID,
        version_number: int,
        tenant_id: UUID,
    ) -> Optional[MasterDataVersion]:
        """Get specific version of entity
        
        Args:
            entity_id: Entity ID
            version_number: Version number to retrieve
            tenant_id: Tenant ID
            
        Returns:
            Specific version or None
        """
        stmt = select(MasterDataVersion).where(
            and_(
                MasterDataVersion.entity_id == entity_id,
                MasterDataVersion.version_number == version_number,
                MasterDataVersion.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_version_history(
        self,
        entity_id: UUID,
        tenant_id: UUID,
    ) -> list[MasterDataVersion]:
        """Get all versions for entity (sorted by version number)
        
        Args:
            entity_id: Entity ID
            tenant_id: Tenant ID
            
        Returns:
            List of all versions in order
        """
        stmt = (
            select(MasterDataVersion)
            .where(
                and_(
                    MasterDataVersion.entity_id == entity_id,
                    MasterDataVersion.tenant_id == tenant_id,
                )
            )
            .order_by(MasterDataVersion.version_number.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count_entity_versions(
        self,
        entity_id: UUID,
        tenant_id: UUID,
    ) -> int:
        """Count total versions for entity
        
        Args:
            entity_id: Entity ID
            tenant_id: Tenant ID
            
        Returns:
            Number of versions
        """
        stmt = select(MasterDataVersion).where(
            and_(
                MasterDataVersion.entity_id == entity_id,
                MasterDataVersion.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def get_latest_version(
        self,
        entity_id: UUID,
        tenant_id: UUID,
    ) -> Optional[MasterDataVersion]:
        """Get latest version of entity
        
        Args:
            entity_id: Entity ID
            tenant_id: Tenant ID
            
        Returns:
            Latest version or None
        """
        stmt = (
            select(MasterDataVersion)
            .where(
                and_(
                    MasterDataVersion.entity_id == entity_id,
                    MasterDataVersion.tenant_id == tenant_id,
                )
            )
            .order_by(MasterDataVersion.version_number.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_versions_by_type(
        self,
        entity_type: str,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MasterDataVersion]:
        """Get versions for all entities of a type
        
        Args:
            entity_type: Entity type (category/type)
            tenant_id: Tenant ID
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of versions
        """
        stmt = (
            select(MasterDataVersion)
            .where(
                and_(
                    MasterDataVersion.entity_type == entity_type,
                    MasterDataVersion.tenant_id == tenant_id,
                )
            )
            .order_by(MasterDataVersion.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_versions_by_user(
        self,
        changed_by: str,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MasterDataVersion]:
        """Get all changes made by a specific user
        
        Args:
            changed_by: User ID
            tenant_id: Tenant ID
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of versions
        """
        stmt = (
            select(MasterDataVersion)
            .where(
                and_(
                    MasterDataVersion.changed_by == changed_by,
                    MasterDataVersion.tenant_id == tenant_id,
                )
            )
            .order_by(MasterDataVersion.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_versions_since(
        self,
        tenant_id: UUID,
        since_timestamp: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MasterDataVersion]:
        """Get all versions since a specific timestamp
        
        Args:
            tenant_id: Tenant ID
            since_timestamp: ISO 8601 timestamp
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of versions
        """
        from datetime import datetime

        since_dt = datetime.fromisoformat(since_timestamp)
        stmt = (
            select(MasterDataVersion)
            .where(
                and_(
                    MasterDataVersion.tenant_id == tenant_id,
                    MasterDataVersion.created_at >= since_dt,
                )
            )
            .order_by(MasterDataVersion.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
