"""Reusable model mixins.

These are abstract — never registered as concrete tables. Apps inherit from
``TimeStampedUUIDModel`` to gain UUID primary keys, created/updated timestamps,
and soft-delete capability.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDPrimaryKeyModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self) -> tuple[int, dict[str, int]]:  # type: ignore[override]
        return self.update(deleted_at=timezone.now()), {}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()

    def alive(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    def __init__(self, *args: Any, alive_only: bool = True, **kwargs: Any) -> None:
        self._alive_only = alive_only
        super().__init__(*args, **kwargs)

    def get_queryset(self) -> SoftDeleteQuerySet:
        qs = SoftDeleteQuerySet(self.model, using=self._db)
        if self._alive_only:
            qs = qs.filter(deleted_at__isnull=True)
        return qs


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManager(alive_only=False)

    class Meta:
        abstract = True

    def delete(
        self, using: str | None = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:  # type: ignore[override]
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"], using=using)
        return 1, {self._meta.label: 1}

    def hard_delete(
        self, using: str | None = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self) -> None:
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])


class TimeStampedUUIDModel(UUIDPrimaryKeyModel, TimeStampedModel, SoftDeleteModel):
    """Combine UUID PK + timestamps + soft delete. Use as base for entities."""

    class Meta:
        abstract = True
