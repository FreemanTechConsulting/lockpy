
from dataclasses import dataclass


@dataclass
class AcquiredLock:
    lock_key: str
    lock_id: str
    expires_at: str


