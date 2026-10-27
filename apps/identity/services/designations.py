from __future__ import annotations

from apps.organization.models import Designation


def get_designation_name(designation_id: int | None) -> str:
    if not designation_id:
        return ""
    name = Designation.objects.filter(pk=designation_id).values_list("name", flat=True).first()
    return str(name or "").strip()


def resolve_designation_name(designation_id: int | None, designation_name: str | None = None) -> str:
    name = str(designation_name or "").strip()
    if name:
        return name
    return get_designation_name(designation_id)
