from datetime import date

from django.core.management.base import BaseCommand

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

        self.stdout.write(self.style.SUCCESS("Organisation seed complete."))
