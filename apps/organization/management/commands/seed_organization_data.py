from datetime import date

from django.core.management.base import BaseCommand

from apps.identity.models import UserProfile
from apps.organization.models import OrganisationalUnit, OrganisationalUnitHead

# Employee source IDs match the demo users seeded by
# apps.identity.management.commands.seed_auth_data — e0 is the
# super_admin, e1..e4 are the other demo accounts.
UNITS = [
    ("Administration", "DIRECTORATE"),
    ("Finance", "DIRECTORATE"),
    ("Human Resource", "DEPARTMENT"),
    ("ICT", "UNIT"),
    ("Geological Mapping", "UNIT"),
]

HEADS = [
    # (unit name, employeeId, leadershipRole)
    ("Administration", "e1", "HEAD_OF_DIRECTORATE"),
    ("Finance", "e2", "HEAD_OF_DIRECTORATE"),
    ("Human Resource", "e4", "HEAD_OF_DEPARTMENT"),
]

# UserProfile.departmentId ("d1"..) and OrganisationalUnit.name are two
# genuinely separate identifier spaces (see OrganisationalUnit's own
# docstring) — this map only exists to backfill demo/seed data with a
# real organisationalUnitId so claim forms can auto-fill "the requester's
# own directorate/unit" instead of asking them to pick one. A real
# deployment would set UserProfile.organisationalUnitId directly (e.g. via
# the employee admin UI), not rely on name-matching seed data.
DEPARTMENT_ID_TO_UNIT_NAME = {
    "d1": "Administration",
    "d2": "Finance",
    "d3": "ICT",
    "d4": "Human Resource",
    "d5": "Geological Mapping",
}


class Command(BaseCommand):
    help = "Seed demo organisational units and their current heads."

    def handle(self, *args, **options):
        units_by_name = {}
        for name, unit_type in UNITS:
            unit, _ = OrganisationalUnit.objects.update_or_create(
                name=name, defaults={"unitType": unit_type, "isActive": True}
            )
            units_by_name[name] = unit

        for unit_name, employee_id, leadership_role in HEADS:
            OrganisationalUnitHead.objects.get_or_create(
                organisationalUnit=units_by_name[unit_name],
                employeeId=employee_id,
                leadershipRole=leadership_role,
                defaults={
                    "isActing": False,
                    "effectiveFrom": date(2024, 1, 1),
                    "effectiveTo": None,
                    "isActive": True,
                },
            )

        for profile in UserProfile.objects.all():
            unit_name = DEPARTMENT_ID_TO_UNIT_NAME.get(profile.departmentId)
            unit = units_by_name.get(unit_name) if unit_name else None
            if unit and profile.organisationalUnitId != unit.id:
                profile.organisationalUnitId = unit.id
                profile.save(update_fields=["organisationalUnitId"])

        self.stdout.write(self.style.SUCCESS("Organisation seed complete."))
