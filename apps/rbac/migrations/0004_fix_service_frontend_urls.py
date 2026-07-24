import os

from django.db import migrations


def fix_frontend_urls(apps, schema_editor):
    """0003 seeded configuration-service's frontendUrl from a
    CONFIGURATION_FRONTEND_URL env var that defaulted to the old standalone
    configuration_frontend app's port (3000) — an app that no longer exists,
    now merged into the same frontend that serves eda-service. Any database
    where 0003 already ran has that stale URL baked in; correct it here so
    every environment self-heals on its next `migrate`, not just fresh ones.
    """
    Service = apps.get_model("rbac", "Service")
    frontend_base = os.getenv("EDA_FRONTEND_URL", "http://localhost:8081")
    Service.objects.filter(name="eda-service").update(frontendUrl=f"{frontend_base}/eda/dashboard")
    Service.objects.filter(name="configuration-service").update(
        frontendUrl=f"{frontend_base}/configuration/dashboard"
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0003_app_launcher_and_service_access"),
    ]

    operations = [
        migrations.RunPython(fix_frontend_urls, noop_reverse),
    ]
