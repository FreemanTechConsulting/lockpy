import logging
from uuid import UUID

from lockpy.backend import BaseBackend
from lockpy.models import AcquiredLock

logger = logging.getLogger(__name__)


class Lock:
    """
    Class for acquiring a single lock.

    The class is context manager enabled, you can use it in a with statement
    to acquire a lock. The lock is automatically released when the context
    manager exits.

    Example:
    async with Lock('my_lock', 300, DynamoDBLockTable('my_table')):
        # do something that requires the lock
    """

    def __init__(
        self,
        lock_key: str,
        ttl_seconds: int,
        backend: BaseBackend,
    ):
        self.lock_key: str = lock_key
        self.ttl_seconds: int = ttl_seconds
        self.backend: BaseBackend = backend
        self.lock_id: UUID = None

    async def __aenter__(self):
        return await self.acquire()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()

    async def acquire(self) -> AcquiredLock:
        """
        Acquires a lock on the specified lock key.

        :param lock_key: The unique key for the lock.
        :param ttl_seconds: Time-to-live in seconds for the lock.
        :return: AcquiredLock if the lock is acquired, thorws an exception otherwise.
        """
        lock: AcquiredLock = await self.backend.acquire(self.lock_key, self.ttl_seconds)
        self.lock_id = lock.lock_id
        logger.info(f"🔒 Acquired lock for {self.lock_key}")
        return lock

    async def release(self) -> bool:
        """
        Releases a lock on the specified lock key.

        :param lock_key: The unique key for the lock.
        :param lock_id: The ID of the lock to ensure proper ownership.
        :return: True if the lock is relockd, throws an exception otherwise.
        """
        await self.backend.release(self.lock_key, self.lock_id)
        self.lock_id = None
        logger.info(f"🔓 Released lock for {self.lock_key}")
        return True

    async def is_locked(self) -> bool:
        """
        Checks if a lock is currently locked on the specified key.

        :param lock_key: The unique key for the lock.
        :return: True if the lock exists and is not expired, False otherwise.
        """
        return await self.backend.is_locked(self.lock_key)

    async def refresh(self) -> AcquiredLock:
        """
        Refreshes the lock by extending its expiration time.

        :param lock_key: The unique key for the lock.
        :param lock_id: The ID of the lock to ensure proper ownership.
        :param ttl_seconds: The new time-to-live in seconds for the lock.
        :return: The refreshed lock, otherwise throws an exception.
        """
        lock: AcquiredLock = await self.backend.refresh(
            self.lock_key, self.lock_id, self.ttl_seconds
        )
        self.lock_id = lock.lock_id
        logger.info(f"♻️ Refreshed lock for {self.lock_key}")
        return lock


class LockClient:
    def __init__(
        self,
        backend: BaseBackend,
    ):
        self.backend: BaseBackend = backend

    async def acquire(self, lock_key: str, ttl_seconds: int) -> AcquiredLock:
        """
        Acquires a lock on the specified lock key.

        :param lock_key: The unique key for the lock.
        :param ttl_seconds: Time-to-live in seconds for the lock.
        :return: AcquiredLock if the lock is acquired, thorws an exception otherwise.
        """
        lock: AcquiredLock = await self.backend.acquire(lock_key, ttl_seconds)
        logger.info(f"🔒 Acquired lock for {lock_key}")
        return lock

    async def release(self, lock_key: str, lock_id: UUID) -> bool:
        """
        Releases a lock on the specified lock key.

        :param lock_key: The unique key for the lock.
        :param lock_id: The ID of the lock to ensure proper ownership.
        :return: True if the lock is relockd, throws an exception otherwise.
        """
        release: bool = await self.backend.release(lock_key, lock_id)
        logger.info(f"🔓 Released lock for {lock_key}")
        return release

    async def is_locked(self, lock_key: UUID) -> bool:
        """
        Checks if a lock is currently locked on the specified key.

        :param lock_key: The unique key for the lock.
        :return: True if the lock exists and is not expired, False otherwise.
        """
        return await self.backend.is_locked(lock_key)

    async def refresh(self, lock_key, lock_id, ttl_seconds) -> AcquiredLock:
        """
        Refreshes the lock by extending its expiration time.

        :param lock_key: The unique key for the lock.
        :param lock_id: The ID of the lock to ensure proper ownership.
        :param ttl_seconds: The new time-to-live in seconds for the lock.
        :return: The refreshed lock, otherwise throws an exception.
        """
        lock: AcquiredLock = await self.backend.refresh(lock_key, lock_id, ttl_seconds)
        logger.info(f"♻️ Refreshed lock for {self.lock_key}")
        return lock
