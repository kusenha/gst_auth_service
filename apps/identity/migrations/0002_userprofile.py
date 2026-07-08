from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("identity", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sourceUserId", models.CharField(db_index=True, max_length=50, unique=True)),
                ("checkNumber", models.CharField(max_length=50, unique=True)),
                ("personnelNumber", models.CharField(blank=True, db_index=True, max_length=50, null=True, unique=True)),
                ("middleName", models.CharField(blank=True, max_length=120)),
                ("gender", models.CharField(choices=[("Male", "Male"), ("Female", "Female")], default="Male", max_length=10)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("departmentId", models.CharField(blank=True, max_length=50)),
                ("designationId", models.IntegerField(blank=True, null=True)),
                ("designationName", models.CharField(blank=True, max_length=120)),
                ("education", models.CharField(blank=True, max_length=60)),
                ("status", models.CharField(choices=[("Active", "Active"), ("On Leave", "On Leave"), ("Retired", "Retired")], default="Active", max_length=20)),
                ("salaryScale", models.CharField(blank=True, max_length=30)),
                ("dutyStation", models.CharField(blank=True, max_length=120)),
                ("region", models.CharField(blank=True, max_length=120)),
                ("dateEmployed", models.DateField(blank=True, null=True)),
                ("bank", models.CharField(blank=True, max_length=120)),
                ("accountNumber", models.CharField(blank=True, max_length=50)),
                ("taxNumber", models.CharField(blank=True, max_length=50)),
                ("nida", models.CharField(blank=True, max_length=50)),
                ("supervisorId", models.CharField(blank=True, max_length=50)),
                ("photo", models.URLField(blank=True)),
                ("role", models.CharField(default="employee", max_length=80)),
                ("mustChangePassword", models.BooleanField(default=False)),
                ("accountEmailStatus", models.CharField(default="not_sent", max_length=30)),
                ("accountEmailSentAt", models.DateTimeField(blank=True, null=True)),
                ("accountEmailError", models.TextField(blank=True)),
                ("createdAt", models.DateTimeField(auto_now_add=True)),
                ("updatedAt", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
    ]
