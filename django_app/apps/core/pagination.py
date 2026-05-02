"""Cursor pagination for stable, fast paging over large result sets."""

from __future__ import annotations

from rest_framework.pagination import CursorPagination


class CursorPagePagination(CursorPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = "-created_at"
