import django.db.models.deletion
from django.db import migrations, models


def migrate_role_service_to_fk(apps, schema_editor):
    Role = apps.get_model("rbac", "Role")
    Service = apps.get_model("rbac", "Service")
    for role in Role.objects.all():
        name = (role.serviceName or "").strip().lower()
        if not name:
            continue
        service, _ = Service.objects.get_or_create(name=name, defaults={"displayName": name})
        role.service = service
        role.save(update_fields=["service"])


def reverse_role_service_to_fk(apps, schema_editor):
    Role = apps.get_model("rbac", "Role")
    for role in Role.objects.all():
        role.serviceName = role.service.name if role.service_id else ""
        role.save(update_fields=["serviceName"])


class Migration(migrations.Migration):

    dependencies = [
        ("rbac", "0001_initial"),
    ]

    operations = [
        # --- Role: replace the plain "service" string with a real FK to Service ---
        migrations.RemoveConstraint(
            model_name="role",
            name="unique_service_role_key",
        ),
        migrations.RenameField(
            model_name="role",
            old_name="service",
            new_name="serviceName",
        ),
        migrations.AlterField(
            model_name="role",
            name="serviceName",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="role",
            name="service",
            field=models.ForeignKey(
                blank=True,
                help_text="Null = a global role usable by any service (e.g. super_admin).",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="roles",
                to="rbac.service",
            ),
        ),
        migrations.RunPython(migrate_role_service_to_fk, reverse_role_service_to_fk),
        migrations.RemoveField(
            model_name="role",
            name="serviceName",
        ),
        migrations.AddConstraint(
            model_name="role",
            constraint=models.UniqueConstraint(fields=("service", "key"), name="unique_service_role_key"),
        ),
        migrations.AlterModelOptions(
            name="role",
            options={"ordering": ["service__name", "key"]},
        ),
        # --- Permission: drop the per-permission service field; key is globally unique ---
        migrations.RemoveConstraint(
            model_name="permission",
            name="unique_service_permission_key",
        ),
        migrations.RemoveField(
            model_name="permission",
            name="service",
        ),
        migrations.AlterField(
            model_name="permission",
            name="key",
            field=models.CharField(db_index=True, max_length=100, unique=True),
        ),
        migrations.AlterModelOptions(
            name="permission",
            options={"ordering": ["key"]},
        ),
    ]
