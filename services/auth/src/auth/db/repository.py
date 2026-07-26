"""Database queries for auth service."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import APIKey, Tenant


class APIKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_hash(self, key_hash: str) -> APIKey | None:
        result = await self._session.execute(
            select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_tenant(self, tenant_id: str) -> Tenant | None:
        result = await self._session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def touch_last_used(self, key_id: str) -> None:
        """Non-blocking update of last_used_at — fire and forget acceptable."""
        await self._session.execute(
            update(APIKey)
            .where(APIKey.id == key_id)
            .values(last_used_at=datetime.now(timezone.utc))
        )
        await self._session.commit()

    async def create(
        self,
        tenant_id: str,
        key_hash: str,
        key_prefix: str,
        name: str,
        scopes: list[str],
        expires_at: datetime | None = None,
    ) -> APIKey:
        key = APIKey(
            tenant_id=tenant_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            scopes=scopes,
            expires_at=expires_at,
        )
        self._session.add(key)
        await self._session.commit()
        await self._session.refresh(key)
        return key

    async def revoke(self, key_id: str, tenant_id: str) -> bool:
        result = await self._session.execute(
            update(APIKey)
            .where(APIKey.id == key_id, APIKey.tenant_id == tenant_id)
            .values(is_active=False)
            .returning(APIKey.id)
        )
        await self._session.commit()
        return result.scalar_one_or_none() is not None
