class BaseBackend:
    def __init__(self):
        pass

    def acquire(self, lock_key, ttl_seconds):
        raise NotImplementedError

    def release(self, lock_key, lock_id):
        raise NotImplementedError

    def is_locked(self, lock_key):
        raise NotImplementedError

    async def refresh(self, lock_key, lock_id, ttl_seconds):
        raise NotImplementedError
