import os

from django.db import migrations


def seed_claims_launcher_entry(apps, schema_editor):
    from django.contrib.auth import get_user_model

    Service = apps.get_model("rbac", "Service")
    UserModel = get_user_model()
    UserServiceAccess = apps.get_model("rbac", "UserServiceAccess")

    # Same merged frontend that serves eda-service and configuration-service —
    # see gst_auth_service/apps/rbac/migrations/0003_app_launcher_and_service_access.py.
    frontend_base = os.getenv("EDA_FRONTEND_URL", "http://localhost:8081")

    claims_service, _ = Service.objects.get_or_create(
        name="claim-request-service",
        defaults={"displayName": "Claims & Requests"},
    )
    claims_service.showInLauncher = True
    claims_service.frontendUrl = f"{frontend_base}/claims/dashboard"
    claims_service.icon = "🧾"
    claims_service.color = "#8E24AA"
    claims_service.sortOrder = 3
    if not claims_service.displayName:
        claims_service.displayName = "Claims & Requests"
    claims_service.save(
        update_fields=["showInLauncher", "frontendUrl", "icon", "color", "sortOrder", "displayName"]
    )

    # Every active employee is a potential submitter of a claim/imprest
    # request — grant access to all of them up front, matching eda-service's
    # own precedent in 0003, rather than requiring an admin to grant it by
    # hand on the App Access screen before anyone can even see the module.
    for user in UserModel.objects.filter(is_active=True):
        UserServiceAccess.objects.get_or_create(user_id=user.pk, service=claims_service)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0005_drop_global_role_duplicates"),
    ]

    operations = [
        migrations.RunPython(seed_claims_launcher_entry, noop_reverse),
    ]
