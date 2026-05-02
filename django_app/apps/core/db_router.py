"""Primary/replica DB router.

Reads go to the read replica when configured; writes always go to default.
"""

from __future__ import annotations

import random
from typing import Any


class PrimaryReplicaRouter:
    READ_DB = "read_replica"
    WRITE_DB = "default"

    def db_for_read(self, model: Any, **hints: Any) -> str:
        from django.conf import settings

        if "read_replica" in settings.DATABASES:
            return random.choice([self.READ_DB, self.WRITE_DB])
        return self.WRITE_DB

    def db_for_write(self, model: Any, **hints: Any) -> str:
        return self.WRITE_DB

    def allow_relation(self, *args: Any, **kwargs: Any) -> bool:
        return True

    def allow_migrate(self, db: str, app_label: str, *args: Any, **kwargs: Any) -> bool:
        return db == self.WRITE_DB
