import aioboto3
from datetime import datetime, timedelta, timezone
import uuid
import logging
from botocore.exceptions import ClientError

from lockpy.backend.base_backend import BaseBackend
from lockpy.models.exceptions import DuplicateLockError, RefreshLockError
from lockpy.models.lock import AcquiredLock

logger = logging.getLogger(__name__)


class DynamoDBlockTable(BaseBackend):
    def __init__(self, table_name, partition_key):
        self.table_name = table_name
        self.partition_key = partition_key
        self._session = aioboto3.Session()

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, session):
        self._session = session

    async def acquire(self, lock_key, ttl_seconds):
        """
        Acquires a lock on the specified resource key.

        :param lock_key: The unique key for the lock.
        :param ttl_seconds: Time-to-live in seconds for the lock.
        :return: True if the lock is acquired, False otherwise.
        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)

            lock_id = str(uuid.uuid4())
            expiration_time = (
                datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            ).isoformat()
            try:
                await table.put_item(
                    Item={
                        self.partition_key: lock_key,
                        "lock_id": lock_id,
                        "expires_at": expiration_time,
                    },
                    ConditionExpression=f"attribute_not_exists({self.partition_key}) OR expires_at < :now",
                    ExpressionAttributeValues={
                        ":now": datetime.now(timezone.utc).isoformat()
                    },
                )
                return AcquiredLock(lock_key, lock_id, expiration_time)
            except ClientError as client_error:
                if (
                    client_error.response["Error"]["Code"]
                    == "ConditionalCheckFailedException"
                ):
                    logger.error(f"key {lock_key} already locked")
                    raise DuplicateLockError(f"key {lock_key} already locked")
                logger.error(f"Unknown error failed to acquire lock for {lock_key}")
                logger.debug(client_error)
                raise client_error
            except Exception as e:
                logger.error(f"Unknown error failed to acquire lock for {lock_key}")
                logger.debug(e)
                raise e

    async def release(self, lock_key, lock_id):
        """
        Relocks a lock on the specified key.

        :param lock_key: The unique key for the lock.
        :param lock_id: The ID of the lock to ensure proper ownership.
        :return: True if the lock is relockd, False otherwise.
        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)

            try:
                await table.delete_item(
                    Key={self.partition_key: lock_key},
                    ConditionExpression="lock_id = :lock_id",
                    ExpressionAttributeValues={":lock_id": lock_id},
                )
                return True
            except Exception as e:
                logger.error(f"Failed to relock lock for {lock_key}: {e}")
                return False

    async def is_locked(self, lock_key):
        """
        Checks if a lock is active on the specified key.

        :param lock_key: The unique key for the lock.
        :return: True if the lock exists and is not expired, False otherwise.
        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)

            response = await table.get_item(Key={self.partition_key: lock_key})
            item = response.get("Item")
            if not item:
                return False

            # Check if the lock has expired
            expires_at = datetime.fromisoformat(item["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                # lock is expired
                await table.delete_item(Key={self.partition_key: lock_key})
                return False

            return True

    async def refresh(self, lock_key, lock_id, ttl_seconds):
        """
        Refreshes the lock by extending its expiration time.

        :param lock_key: The unique key for the lock.
        :param lock_id: The ID of the lock to ensure proper ownership.
        :param ttl_seconds: The new time-to-live in seconds for the lock.
        :return: True if the lock is refreshed, False otherwise.
        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)

            new_expiration_time = (
                datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            ).isoformat()

            try:
                await table.update_item(
                    Key={self.partition_key: lock_key},
                    UpdateExpression="SET expires_at = :new_expiration",
                    ConditionExpression="lock_id = :lock_id",
                    ExpressionAttributeValues={
                        ":new_expiration": new_expiration_time,
                        ":lock_id": lock_id,
                    },
                )
                return AcquiredLock(lock_key, lock_id, new_expiration_time)
            except ClientError as client_error:
                if (
                    client_error.response["Error"]["Code"]
                    == "ConditionalCheckFailedException"
                ):
                    logger.error(f"Failed to refresh lock for {lock_key}")
                    raise RefreshLockError(f"Failed to refresh lock for {lock_key}")
            except Exception as e:
                logger.error(f"Failed to refresh lock for {lock_key}")
                logger.debug(e)
                raise RefreshLockError(f"Failed to refresh lock for {lock_key}")
