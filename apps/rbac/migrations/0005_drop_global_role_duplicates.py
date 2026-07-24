from django.db import migrations

# Roles used to be registered globally (service=null) — see the old
# rbac_catalog.py in eda-service before it switched to registering them
# scoped to itself, matching every other per-service row. Once that switch
# lands, register_rbac stops touching these null-service rows entirely, so
# they'd sit around unmaintained (never getting new permission keys) while
# resolve_permission_keys() unions across every row sharing a role key —
# silently pulling in their stale permission set forever. Drop them; the
# already-existing eda-service-scoped rows with the same keys take over.
KNOWN_ROLE_KEYS = [
    "employee",
    "department_head",
    "finance_officer",
    "hr_officer",
    "administrator",
    "super_admin",
]


def drop_global_duplicates(apps, schema_editor):
    Role = apps.get_model("rbac", "Role")
    Role.objects.filter(service__isnull=True, key__in=KNOWN_ROLE_KEYS).delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0004_fix_service_frontend_urls"),
    ]

    operations = [
        migrations.RunPython(drop_global_duplicates, noop_reverse),
    ]
