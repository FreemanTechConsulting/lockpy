# lockpy


`lockpy` is a Python library for acquiring and releasing distributed locks. It provides a simple interface for acquiring and releasing locks.

It solves the problem in distributed systems where you may have two different instances running and you want to ensure that only one instance acquires the lock at a time. lockpy is meant to be simple and easy to use.

Right now it only supports dynamodb but other backends are planned.

Here are some features of `lockpy`:
 - implemented using asyncio
 - allows for auto-renewal of locks
 - can be used as an asyncio context manager

## Installation

You can install `lockpy` using pip:

```
git clone https://github.com/dbfreem/lockpy.git
cd lockpy
pip install .
```

## Usage

Here's an example of how to use `lockpy`:

```python
from lockpy import Lock

lock = Lock("my_lock_key")

if await lock.acquire():
    try:
        # Do some work here
        pass
    finally:
        await lock.release()
```

In this example, we create a `Lock` object with a key of "my_lock_key". We then call the `acquire()` method to acquire the lock. If the lock is acquired successfully, we do some work and then call the `release()` method to release the lock.

`lockpy` supports multiple locking backends, including Redis and DynamoDB. You can specify the backend to use when creating the `Lock` object. For example, to use Redis as the locking backend, you can do the following:

```python
from lockpy import Lock
from lockpy.backends.redis import RedisBackend

redis_client = redis.Redis()

lock = Lock("my_lock_key", backend=RedisBackend(redis_client))
```

In this example, we create a `RedisBackend` object using a `redis.Redis` client, and pass it to the `Lock` constructor.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.

## License

`lockpy` is licensed under the MIT License.
