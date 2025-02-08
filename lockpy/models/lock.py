from dataclasses import dataclass
from uuid import UUID


@dataclass
class AcquiredLock:
    lock_key: str
    lock_id: UUID
    expires_at: str
