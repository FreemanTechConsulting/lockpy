The API is still being refined on lockpy and may change in the future. If you have any ideas or want to contribute, please create an issue or pull request.

# lockpy

`lockpy` is a Python library for acquiring and releasing distributed locks. It provides a simple interface for acquiring and releasing locks.

It solves the problem in distributed systems where you may have two different instances running and you want to ensure that only one instance acquires the lock at a time. lockpy is meant to be simple and easy to use.

Right now it only supports dynamodb but other backends are planned.

Here are some features of `lockpy`:
 - implemented using asyncio
 - can be used as an asyncio context manager

## Python Versions supported
Currently supported for python 3.9 to 3.13

## Installation

Not yet posted to pypi but coming soon!

You can install `lockpy` using pip:

```
git clone https://github.com/dbfreem/lockpy.git
cd lockpy
pip install .
```

## Usage

### Context Manager
Below is an example of using `Lock` as a context manager

```python
from lockpy import Lock

async with Lock(
    lock_key,
    ttl_seconds,
    DynamoDBlockTable(table_name="test_lock", partition_key="lock_key")
) as lock:
    # Do some work here
    pass
```

### Using LockClient

LockClient can be used if a context manager is not desired. Also using LockClient will allow for generating multiple locks at different lock keys

```python
from lockpy import LockClient

lock_client = LockClient(DynamoDBlockTable(table_name="test_lock", partition_key="lock_key"))
lock = await lock_client.acquire(lock_key, ttl_seconds)
print(await lock_client.is_locked(lock_key))
await lock_client.refresh(lock_key, lock.lock_id, ttl_seconds)
if await lock_client.is_locked(lock_key):
    await lock_client.release(lock_key, lock.lock_id)
```
In this example we use the LockClient to acquire a lock on 
In this example, we create a `Lock` object with a key of "my_lock_key". We then call the `acquire()` method to acquire the lock. If the lock is acquired successfully, we do some work and then call the `release()` method to release the lock.

`lockpy` supports multiple locking backends, including Redis and DynamoDB. You can specify the backend to use when creating the `Lock` object. For example, to use Redis as the locking backend, you can do the following:


## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.

## License

`lockpy` is licensed under the MIT License.
