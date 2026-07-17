from django.core.management.base import BaseCommand

from apps.rbac.models import Permission, Role, RolePermission, Service

# Migrated from eda_frontend/src/lib/permissions.ts, the source of truth that was
# actually driving access-control behavior (via hasPermission's static fallback matrix)
# while the backend's own catalog was Django-generated noise. See permissionRoles there.
PERMISSIONS = [
    ("dashboard.view", "View dashboard", ""),
    ("notifications.view", "View notifications", ""),
    ("tasks.view", "View tasks", ""),
    ("tasks.manage", "Manage tasks", ""),
    ("attendance.view", "View attendance", ""),
    ("attendance.record", "Record attendance", ""),
    ("requests.view", "View EDA requests", ""),
    ("requests.create", "Create EDA requests", ""),
    ("approvals.view", "View approvals", ""),
    ("approvals.process", "Process approvals", ""),
    ("finance.view", "View finance", ""),
    ("finance.process", "Process finance", ""),
    ("payments.view", "View payments", ""),
    ("employees.view", "View employees", ""),
    ("employees.manage", "Manage employees", ""),
    ("departments.view", "View departments", ""),
    ("departments.manage", "Manage departments", ""),
    ("reports.view", "View reports", ""),
    ("analytics.view", "View analytics", ""),
    ("settings.view", "View settings", ""),
    ("settings.manage", "Manage settings", ""),
    ("audit.view", "View audit logs", ""),
    ("profile.view", "View own profile", ""),
]

ALL_KEYS = [key for key, _, _ in PERMISSIONS]

_APPROVER = ["approvals.view", "approvals.process"]
_FINANCE = ["finance.view", "finance.process", "payments.view"]

ROLES = {
    "employee": [
        "dashboard.view", "notifications.view", "tasks.view", "attendance.view",
        "requests.view", "requests.create", "departments.view", "profile.view",
    ],
    "department_head": [
        "dashboard.view", "notifications.view", "tasks.view", "attendance.view",
        "attendance.record", "requests.view", "requests.create", *_APPROVER,
        "employees.view", "departments.view", "reports.view", "profile.view",
    ],
    "finance_officer": [
        "dashboard.view", "notifications.view", "tasks.view", "attendance.view",
        "requests.view", "requests.create", *_APPROVER, *_FINANCE,
        "departments.view", "reports.view", "profile.view",
    ],
    "hr_officer": [
        "dashboard.view", "notifications.view", "tasks.view", "attendance.view",
        "attendance.record", "requests.view", "requests.create", "employees.view",
        "employees.manage", "departments.view", "departments.manage", "reports.view",
        "profile.view",
    ],
    "administrator": ALL_KEYS,
    "super_admin": ALL_KEYS,
}


class Command(BaseCommand):
    help = "Seed the eda-service permission catalog and its six roles into the RBAC registry."

    def handle(self, *args, **options):
        # Registers "eda-service" in the service catalog. Permissions are a
        # global vocabulary (no service field of their own); this service is
        # simply the first, and currently only, consumer of them.
        Service.touch("eda-service", display_name="EDA Service")

        permission_by_key = {}
        for key, name, description in PERMISSIONS:
            permission, _ = Permission.objects.update_or_create(
                key=key,
                defaults={"name": name, "description": description},
            )
            permission_by_key[key] = permission

        for role_key, permission_keys in ROLES.items():
            role, _ = Role.objects.get_or_create(
                service=None,
                key=role_key,
                defaults={"name": role_key.replace("_", " ").title(), "isSystem": True},
            )
            if not role.isSystem:
                role.isSystem = True
                role.save(update_fields=["isSystem"])

            existing_ids = set(RolePermission.objects.filter(role=role).values_list("permission_id", flat=True))
            wanted_ids = {permission_by_key[key].id for key in permission_keys}
            RolePermission.objects.bulk_create(
                [RolePermission(role=role, permission_id=pid) for pid in wanted_ids - existing_ids]
            )

        self.stdout.write(self.style.SUCCESS("RBAC seed complete."))
