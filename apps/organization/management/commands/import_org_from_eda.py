from django.core.management.base import BaseCommand
from django.db import connections, transaction

from apps.organization.management.commands.seed_organization_data import _reset_designation_sequence
from apps.organization.models import Department, Designation


class Command(BaseCommand):
    help = (
        "One-time move of departments and designations from eda-service's database into "
        "auth_service, which now owns them. Keeps ids. Does nothing if auth already has "
        "departments or the eda_source database isn't configured."
    )

    def handle(self, *args, **options):
        if Department.objects.exists():
            self.stdout.write("Departments already present in auth_service; nothing to import.")
            return
        if "eda_source" not in connections.databases:
            self.stdout.write("No eda_source database configured; nothing to import.")
            return

        try:
            with connections["eda_source"].cursor() as cursor:
                cursor.execute("SELECT id, name, \"headId\", description FROM organization_department")
                departments = cursor.fetchall()
                cursor.execute("SELECT id, department_id, name FROM organization_designation")
                designations = cursor.fetchall()
        except Exception as exc:  # eda-service not migrated yet, unreachable, etc.
            self.stdout.write(self.style.WARNING(f"Could not read eda-service org data: {exc}"))
            return

        with transaction.atomic():
            for dep_id, name, head_id, description in departments:
                Department.objects.create(id=dep_id, name=name, headId=head_id or "", description=description or "")
            for designation_id, dep_id, name in designations:
                Designation.objects.create(id=designation_id, department_id=dep_id, name=name)
        _reset_designation_sequence()
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(departments)} department(s) and {len(designations)} designation(s) from eda-service."
            )
        )
