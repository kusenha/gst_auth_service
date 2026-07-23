from django.core.management.base import BaseCommand

from apps.rbac.models import Service
from apps.rbac.services import grant_service_access_to_admins


class Command(BaseCommand):
    help = (
        "Grants every administrator/super_admin account access to every "
        "registered service. Runs on every auth-service startup so admin "
        "access to a service never depends on that service having called "
        "the RBAC self-registration endpoint (or a human remembering to "
        "grant it by hand on the App Access screen)."
    )

    def handle(self, *args, **options):
        granted = sum(
            grant_service_access_to_admins(service, granted_by="system:sync-admin-access")
            for service in Service.objects.all()
        )
        self.stdout.write(self.style.SUCCESS(f"Admin access sync complete: {granted} grant(s) created."))
