from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, Mock
from botocore.exceptions import ClientError
import pytest

from lockpy.backend import DynamoDBlockTable
from lockpy.models.exceptions import DuplicateLockError, RefreshLockError


class MockSession:

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._resource = MockResource(self.kwargs)
    
    def resource(self, *args, **kwargs):
        return self._resource

class MockResource:

    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.dynamodb = MockDynamo(self.kwargs)

    async def __aenter__(self):
        return self.dynamodb 
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class MockDynamo:

    def __init__(self, kwargs):
        self.kwargs = kwargs
        self._Table = MockTable(self.kwargs)

    async def Table(self, *args, **kwargs):
        return self._Table

class MockTable:

    def __init__(self, kwargs):
        self.kwargs = kwargs

    async def get_item(self, Key):

       return self.kwargs.get("get_item", {
            "Item": {
                "lock_key": "test_key",
                "lock_id": "test_id",
                "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()
            }
        })

    async def put_item(self, *args, **kwargs):
        if self.kwargs.get("put_item") == "ClientError":
            raise  ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, "test")
        return self.kwargs.get("put_item", None)

    
    async def delete_item(self, *args, **kwargs):
        return self.kwargs.get("delete_item", None)
    
    async def update_item(self, *args, **kwargs):
        if self.kwargs.get("update_item") == "ClientError":
            raise  ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, "test")
        return self.kwargs.get("update_item", None)


@pytest.mark.asyncio
async def test_dynamo_lock(monkeypatch):
    lock = DynamoDBlockTable("test_lock", "lock_key")
    monkeypatch.setattr(lock, "session", MockSession(get_item={"Item": {"expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()}}))
    lock_object = await lock.acquire("test_key", 300)
    assert lock_object is not None
    assert lock_object.lock_id is not None
    assert await lock.is_locked("test_key")

@pytest.mark.asyncio
async def test_dynamo_lock_duplicate(monkeypatch):
    lock = DynamoDBlockTable("test_lock", "lock_key")
    monkeypatch.setattr(lock, "session", MockSession(put_item="ClientError"))
    with pytest.raises(DuplicateLockError):
        await lock.acquire("test_key", 300)


@pytest.mark.asyncio
async def test_dynamo_refresh_wrong_id(monkeypatch):
    lock = DynamoDBlockTable("test_lock", "lock_key")
    monkeypatch.setattr(lock, "session", MockSession(update_item="ClientError"))
    with pytest.raises(RefreshLockError):
        await lock.refresh("test_key", "wrong_id", 300)


@pytest.mark.asyncio
async def test_dynamo_refresh(monkeypatch):
    lock = DynamoDBlockTable("test_lock", "lock_key")
    monkeypatch.setattr(lock, "session", MockSession())
    lock_object = await lock.acquire("test_key", 300)
    await lock.refresh("test_key", lock_object.lock_id, 300)
