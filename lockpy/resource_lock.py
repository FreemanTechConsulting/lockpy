from uuid import UUID

from lockpy.lock.baselock import BaseLock


class ResourceLock:
    def __init__(self, backend: BaseLock):
        self.backend: BaseLock = backend

    def acquire(self, lock_key: str, ttl_seconds: int) -> str:
        return self.backend.acquire_lock(lock_key, ttl_seconds)

    def release(self, lock_key: str, lock_id: UUID) -> bool:
        return self.backend.release_lock(lock_key, lock_id)

    def is_locked(self, lock_key: UUID) -> bool:
        return self.backend.is_locked(lock_key)

    async def refresh(self, lock_key, lock_id, ttl_seconds):
        return await self.backend.refresh(lock_key, lock_id, ttl_seconds)
