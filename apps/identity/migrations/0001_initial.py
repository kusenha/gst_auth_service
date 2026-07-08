from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ServiceClient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("clientId", models.CharField(max_length=120, unique=True)),
                ("clientSecret", models.CharField(max_length=200)),
                ("active", models.BooleanField(default=True)),
                ("createdAt", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="RefreshTokenAudit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("userId", models.IntegerField(db_index=True)),
                ("jti", models.CharField(max_length=255, unique=True)),
                ("createdAt", models.DateTimeField(auto_now_add=True)),
                ("revokedAt", models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
