import os

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def seed_apps_and_grants(apps, schema_editor):
    from django.contrib.auth import get_user_model

    Service = apps.get_model("rbac", "Service")
    UserModel = get_user_model()
    UserServiceAccess = apps.get_model("rbac", "UserServiceAccess")

    # One merged frontend serves both apps (eda-service under /eda,
    # configuration-service under /configuration) — both tiles derive their
    # URL from the same base rather than configuration-service having its
    # own separate (and long-retired) standalone frontend/port.
    frontend_base = os.getenv("EDA_FRONTEND_URL", "http://localhost:8081")

    eda_service, _ = Service.objects.get_or_create(
        name="eda-service",
        defaults={"displayName": "EDA Service"},
    )
    eda_service.showInLauncher = True
    eda_service.frontendUrl = f"{frontend_base}/eda/dashboard"
    eda_service.icon = "📋"
    eda_service.color = "#005A9C"
    eda_service.sortOrder = 1
    if not eda_service.displayName:
        eda_service.displayName = "EDA Service"
    eda_service.save(update_fields=["showInLauncher", "frontendUrl", "icon", "color", "sortOrder", "displayName"])

    config_service, _ = Service.objects.get_or_create(
        name="configuration-service",
        defaults={"displayName": "Configuration"},
    )
    config_service.showInLauncher = True
    config_service.frontendUrl = f"{frontend_base}/configuration/dashboard"
    config_service.icon = "⚙️"
    config_service.color = "#1B5E20"
    config_service.sortOrder = 2
    if not config_service.displayName:
        config_service.displayName = "Configuration"
    config_service.save(
        update_fields=["showInLauncher", "frontendUrl", "icon", "color", "sortOrder", "displayName"]
    )

    # Preserve continuity for existing users: everyone active keeps the EDA
    # app they already use daily; administrators/super-admins keep the
    # Configuration access they already had under the old role-only gate.
    # (user_id=... rather than user=... because the live User instance from
    # get_user_model() isn't an instance of this migration's frozen
    # historical User model, which get_or_create would otherwise reject.)
    for user in UserModel.objects.filter(is_active=True):
        UserServiceAccess.objects.get_or_create(user_id=user.pk, service=eda_service)

        profile = getattr(user, "profile", None)
        role = profile.role if profile and profile.role else ""
        if not role:
            role = ",".join(user.groups.values_list("name", flat=True))
        if role in {"administrator", "super_admin"} or "administrator" in role or "super_admin" in role:
            UserServiceAccess.objects.get_or_create(user_id=user.pk, service=config_service)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0002_role_service_fk_permission_global"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="showInLauncher",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="service",
            name="frontendUrl",
            field=models.URLField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="service",
            name="icon",
            field=models.CharField(blank=True, help_text="An emoji shown on the app tile.", max_length=10),
        ),
        migrations.AddField(
            model_name="service",
            name="color",
            field=models.CharField(
                blank=True, help_text="Accent hex color for the app tile, e.g. #005A9C.", max_length=7
            ),
        ),
        migrations.AddField(
            model_name="service",
            name="sortOrder",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name="service",
            options={"ordering": ["sortOrder", "name"]},
        ),
        migrations.CreateModel(
            name="UserServiceAccess",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("grantedAt", models.DateTimeField(auto_now_add=True)),
                ("grantedBy", models.CharField(blank=True, max_length=150)),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="userGrants", to="rbac.service"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="serviceAccess",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="userserviceaccess",
            constraint=models.UniqueConstraint(fields=("user", "service"), name="unique_user_service_access"),
        ),
        migrations.RunPython(seed_apps_and_grants, noop_reverse),
    ]
