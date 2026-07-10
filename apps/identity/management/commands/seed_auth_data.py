from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.identity.models import UserProfile


class Command(BaseCommand):
    help = "Seed auth service users, roles, and profiles."

    def handle(self, *args, **options):
        user_model = get_user_model()

        role_names = [
            "super_admin",
            "administrator",
            "department_head",
            "finance_officer",
            "hr_officer",
            "employee",
        ]
        role_map = {name: Group.objects.get_or_create(name=name)[0] for name in role_names}

        users = [
            {
                "source_id": "e0",
                "check_number": "GST-10000",
                "first_name": "System",
                "last_name": "Administrator",
                "email": "system.administrator@gst.go.tz",
                "role": "super_admin",
                "department_id": "d1",
                "designation_id": 1,
                "designation_name": "Director",
                "education": "PhD",
            },
            {
                "source_id": "e1",
                "check_number": "GST-10001",
                "first_name": "Amani",
                "last_name": "Mwakalinga",
                "email": "amani.mwakalinga@gst.go.tz",
                "role": "department_head",
                "department_id": "d1",
                "designation_id": 2,
                "designation_name": "Manager",
                "education": "Masters",
            },
            {
                "source_id": "e2",
                "check_number": "GST-10002",
                "first_name": "Baraka",
                "last_name": "Kimaro",
                "email": "baraka.kimaro@gst.go.tz",
                "role": "finance_officer",
                "department_id": "d2",
                "designation_id": 5,
                "designation_name": "Accountant",
                "education": "Bachelor",
            },
            {
                "source_id": "e3",
                "check_number": "GST-10003",
                "first_name": "Neema",
                "last_name": "Mushi",
                "email": "neema.mushi@gst.go.tz",
                "role": "employee",
                "department_id": "d5",
                "designation_id": 3,
                "designation_name": "Senior Geologist",
                "education": "Bachelor",
            },
            {
                "source_id": "e4",
                "check_number": "GST-10004",
                "first_name": "Salma",
                "last_name": "Kessy",
                "email": "salma.kessy@gst.go.tz",
                "role": "hr_officer",
                "department_id": "d4",
                "designation_id": 6,
                "designation_name": "Human Resource Officer",
                "education": "Bachelor",
            },
        ]

        for item in users:
            with transaction.atomic():
                user = self._get_or_create_or_reconcile_user(user_model, item)
                profile = self._upsert_profile(user, item)
                user.groups.set([role_map[profile.role]])

        self.stdout.write(self.style.SUCCESS("Auth seed complete. Demo password for seeded users: demo123"))

    def _get_or_create_or_reconcile_user(self, user_model, item: dict):
        # Match existing users by username or email to keep seed runs idempotent.
        user = user_model.objects.filter(
            Q(username=item["check_number"]) | Q(email=item["email"])
        ).first()

        if user is None:
            user = user_model.objects.create(
                username=item["check_number"],
                email=item["email"],
                first_name=item["first_name"],
                last_name=item["last_name"],
                is_active=True,
            )
        else:
            user.username = item["check_number"]
            user.email = item["email"]
            user.first_name = item["first_name"]
            user.last_name = item["last_name"]
            user.is_active = True
            user.save(update_fields=["username", "email", "first_name", "last_name", "is_active"])

        user.set_password("demo123")
        user.save(update_fields=["password"])
        return user

    def _upsert_profile(self, user, item: dict):
        # Reconcile profile by source id, check number, or linked user to avoid unique collisions.
        profile = UserProfile.objects.filter(
            Q(sourceUserId=item["source_id"]) | Q(checkNumber=item["check_number"]) | Q(user=user)
        ).first()

        profile_values = {
            "user": user,
            "sourceUserId": item["source_id"],
            "checkNumber": item["check_number"],
            "personnelNumber": None,
            "middleName": "",
            "gender": "Male",
            "phone": "+255700000000",
            "departmentId": item["department_id"],
            "designationId": item["designation_id"],
            "designationName": item["designation_name"],
            "education": item["education"],
            "status": "Active",
            "salaryScale": "GSS 8",
            "dutyStation": "GST HQ Dodoma",
            "region": "Dodoma",
            "dateEmployed": date(2020, 1, 10),
            "bank": "CRDB Bank",
            "accountNumber": "1000000001",
            "taxNumber": "TIN-100000001",
            "nida": "19900101000000000000",
            "supervisorId": "",
            "photo": "",
            "role": item["role"],
            "mustChangePassword": False,
            "accountEmailStatus": "not_sent",
            "accountEmailError": "",
        }

        if profile is None:
            return UserProfile.objects.create(**profile_values)

        for field_name, field_value in profile_values.items():
            setattr(profile, field_name, field_value)
        profile.save()
        return profile
