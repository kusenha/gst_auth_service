from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from apps.identity.models import UserProfile


@dataclass
class ImportStats:
    created_users: int = 0
    updated_users: int = 0
    created_profiles: int = 0
    updated_profiles: int = 0


class Command(BaseCommand):
    help = "Import users from EDA accounts_user into auth-service identity tables."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Validate and print results without saving.")
        parser.add_argument(
            "--without-passwords",
            action="store_true",
            help="Do not copy password hashes from accounts_user.password.",
        )

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        copy_passwords = not bool(options["without_passwords"])

        if "eda_source" not in connections.databases:
            raise CommandError(
                "Database alias 'eda_source' is not configured. "
                "Set EDA_SOURCE_DB_NAME and related env vars in auth-service settings."
            )

        rows = self._load_source_users()
        self.stdout.write(self.style.NOTICE(f"Loaded {len(rows)} user records from eda_source.accounts_user"))

        stats = ImportStats()
        ctx = transaction.atomic() if not dry_run else _NoopContext()
        with ctx:
            for row in rows:
                self._upsert_user(row, stats, copy_passwords=copy_passwords, dry_run=dry_run)

        self.stdout.write(
            self.style.SUCCESS(
                "User migration done: "
                f"users(created={stats.created_users}, updated={stats.updated_users}), "
                f"profiles(created={stats.created_profiles}, updated={stats.updated_profiles})"
            )
        )

    def _load_source_users(self) -> list[dict[str, Any]]:
        query = """
            SELECT
                u.*,
                d.name AS designation_name
            FROM accounts_user u
            LEFT JOIN organization_designation d ON d.id = u.designation_id
        """
        with connections["eda_source"].cursor() as cursor:
            cursor.execute(query)
            cols = [col[0] for col in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _upsert_user(self, row: dict[str, Any], stats: ImportStats, *, copy_passwords: bool, dry_run: bool):
        User = get_user_model()

        source_id = str(self._get(row, "id") or "").strip()
        check_number = str(self._get(row, "checkNumber") or self._get(row, "checknumber") or "").strip()
        if not source_id or not check_number:
            self.stdout.write(self.style.WARNING("Skipping row with missing id/checkNumber"))
            return

        user_defaults = {
            "email": str(self._get(row, "email") or "").strip(),
            "first_name": str(self._get(row, "first_name") or "").strip(),
            "last_name": str(self._get(row, "last_name") or "").strip(),
            "is_active": True,
        }

        user = (
            User.objects.select_related("profile").filter(username=check_number).first()
            or User.objects.select_related("profile").filter(email=user_defaults["email"]).first()
        )
        created_user = False
        if not user:
            user = User(username=check_number, **user_defaults)
            if copy_passwords:
                password_hash = str(self._get(row, "password") or "").strip()
                if password_hash:
                    user.password = password_hash
                else:
                    user.set_unusable_password()
            else:
                user.set_unusable_password()
            if not dry_run:
                user.save()
            created_user = True
            stats.created_users += 1
        else:
            user.email = user_defaults["email"]
            user.first_name = user_defaults["first_name"]
            user.last_name = user_defaults["last_name"]
            if copy_passwords:
                password_hash = str(self._get(row, "password") or "").strip()
                if password_hash:
                    user.password = password_hash
            if not dry_run:
                user.save(update_fields=["email", "first_name", "last_name", "password"])
            if not created_user:
                stats.updated_users += 1

        profile_defaults = {
            "sourceUserId": source_id,
            "checkNumber": check_number,
        }
        profile = getattr(user, "profile", None)
        created_profile = False
        if not profile:
            profile = UserProfile(user=user, **profile_defaults)
            created_profile = True

        profile.sourceUserId = source_id
        profile.checkNumber = check_number
        profile.personnelNumber = self._nullable_str(self._get(row, "personnelNumber") or self._get(row, "personnelnumber"))
        profile.middleName = self._str(self._get(row, "middleName"))
        profile.gender = self._str(self._get(row, "gender")) or "Male"
        profile.phone = self._str(self._get(row, "phone"))
        profile.departmentId = self._str(self._get(row, "departmentId"))
        profile.designationId = self._int(self._get(row, "designation_id"))
        profile.designationName = self._str(self._get(row, "designation_name"))
        profile.education = self._str(self._get(row, "education"))
        profile.status = self._str(self._get(row, "status")) or "Active"
        profile.salaryScale = self._str(self._get(row, "salaryScale"))
        profile.dutyStation = self._str(self._get(row, "dutyStation"))
        profile.region = self._str(self._get(row, "region"))
        profile.dateEmployed = self._get(row, "dateEmployed")
        profile.bank = self._str(self._get(row, "bank"))
        profile.accountNumber = self._str(self._get(row, "accountNumber"))
        profile.taxNumber = self._str(self._get(row, "taxNumber"))
        profile.nida = self._str(self._get(row, "nida"))
        profile.supervisorId = self._str(self._get(row, "supervisorId"))
        profile.photo = self._str(self._get(row, "photo"))
        profile.role = self._str(self._get(row, "role")) or "employee"
        profile.mustChangePassword = bool(self._get(row, "mustChangePassword"))
        profile.accountEmailStatus = self._str(self._get(row, "accountEmailStatus")) or "not_sent"
        profile.accountEmailSentAt = self._get(row, "accountEmailSentAt")
        profile.accountEmailError = self._str(self._get(row, "accountEmailError"))

        if not dry_run:
            profile.save()

            if profile.role:
                group, _ = Group.objects.get_or_create(name=profile.role)
                user.groups.set([group])

        if created_profile:
            stats.created_profiles += 1
        else:
            stats.updated_profiles += 1

    @staticmethod
    def _get(row: dict[str, Any], key: str) -> Any:
        return row.get(key)

    @staticmethod
    def _str(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _nullable_str(value: Any) -> str | None:
        raw = Command._str(value)
        return raw or None

    @staticmethod
    def _int(value: Any) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


class _NoopContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
