import os

from django.db import migrations

# The same roles auth_service lets manage users and the org structure.
IDENTITY_ROLES = ["hr_officer", "administrator", "super_admin"]


def seed_identity_launcher_entry(apps, schema_editor):
    Service = apps.get_model("rbac", "Service")
    UserProfile = apps.get_model("identity", "UserProfile")
    UserServiceAccess = apps.get_model("rbac", "UserServiceAccess")

    # Same merged frontend that serves the other modules — see 0006.
    frontend_base = os.getenv("EDA_FRONTEND_URL", "http://localhost:8081")

    service, _ = Service.objects.get_or_create(
        name="identity-service",
        defaults={"displayName": "Identity & Access"},
    )
    service.displayName = "Identity & Access"
    service.description = "Employees, departments, designations, employee import and app access — managed in one place."
    service.showInLauncher = True
    service.frontendUrl = f"{frontend_base}/identity/dashboard"
    service.icon = "🪪"
    service.color = "#00796B"
    service.sortOrder = 4
    service.save()

    for profile in UserProfile.objects.filter(role__in=IDENTITY_ROLES, user__is_active=True):
        UserServiceAccess.objects.get_or_create(
            user_id=profile.user_id, service=service, defaults={"grantedBy": "system:identity-portal"}
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0006_claim_request_service_launcher"),
        ("identity", "0007_userprofile_checknumber_validator"),
    ]

    operations = [
        migrations.RunPython(seed_identity_launcher_entry, noop_reverse),
    ]
