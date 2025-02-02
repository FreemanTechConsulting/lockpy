from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, Mock
from botocore.exceptions import ClientError
import pytest

from lockpy.backend import DynamoDBlockTable
from lockpy.models.exceptions import DuplicateLockError


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
        return
    
    async def delete_item(self, *args, **kwargs):
        return
    
    async def update_item(self, *args, **kwargs):
        return 


@pytest.fixture
def mock_dynamodb(mocker):
    mock_dynamodb = mocker.patch.object(DynamoDBlockTable, "session", return_value=MockSession())
    return mock_dynamodb


@pytest.mark.asyncio
async def test_dynamo_lock(monkeypatch, mocker):
    lock = DynamoDBlockTable("test_lock")
    monkeypatch.setattr(lock, "session", MockSession())
    lock_id = await lock.acquire_lock("test_key", 300)
    assert await lock.is_locked("test_key")
    await lock.release_lock("test_key", lock_id)

@pytest.mark.asyncio
async def test_dynamo_locked(monkeypatch):

    lock = DynamoDBlockTable("test_lock")
    session = MockSession()
    
    monkeypatch.setattr(session._resource.dynamodb._Table, "put_item", AsyncMock(side_effect=ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, "test")))
    monkeypatch.setattr(lock, "session", session)
    with pytest.raises(DuplicateLockError):
        lock_id = await lock.acquire_lock("test_key", 300)
