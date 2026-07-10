from __future__ import annotations

from functools import lru_cache

from django.db import connections


@lru_cache(maxsize=512)
def get_designation_name(designation_id: int | None) -> str:
    if not designation_id:
        return ""
    if "eda_source" not in connections.databases:
        return ""

    with connections["eda_source"].cursor() as cursor:
        cursor.execute(
            "SELECT name FROM organization_designation WHERE id = %s LIMIT 1",
            [designation_id],
        )
        row = cursor.fetchone()
    if not row:
        return ""
    return str(row[0] or "").strip()


def resolve_designation_name(designation_id: int | None, designation_name: str | None = None) -> str:
    name = str(designation_name or "").strip()
    if name:
        return name
    return get_designation_name(designation_id)
