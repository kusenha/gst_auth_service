"""Renumber the seeded demo accounts from GST-1000x to 9-digit check numbers.

Check numbers are the login username, so the user, the profile and the
`grantedBy` audit text on access grants all change together. Rows whose new
number is already taken are left alone rather than merged.
"""

from django.db import migrations

RENUMBER = {
    "GST-10000": "100000000",
    "GST-10001": "100000001",
    "GST-10002": "100000002",
    "GST-10003": "100000003",
    "GST-10004": "100000004",
}


def _apply(apps, mapping):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("identity", "UserProfile")
    UserServiceAccess = apps.get_model("rbac", "UserServiceAccess")
    EmployeeImportBatch = apps.get_model("identity", "EmployeeImportBatch")

    for old, new in mapping.items():
        if User.objects.filter(username=new).exists() or UserProfile.objects.filter(checkNumber=new).exists():
            continue
        User.objects.filter(username=old).update(username=new)
        UserProfile.objects.filter(checkNumber=old).update(checkNumber=new)
        UserServiceAccess.objects.filter(grantedBy=old).update(grantedBy=new)
        EmployeeImportBatch.objects.filter(createdBy=old).update(createdBy=new)


def forwards(apps, schema_editor):
    _apply(apps, RENUMBER)


def backwards(apps, schema_editor):
    _apply(apps, {new: old for old, new in RENUMBER.items()})


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0005_userprofile_organisationalunitid"),
        ("rbac", "0006_claim_request_service_launcher"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
