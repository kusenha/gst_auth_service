from __future__ import annotations

import secrets

from django.db import transaction
from django.utils import timezone

from apps.identity.services.account_notifications import send_temporary_password_email
from apps.identity.services.profiles import ProfileConflictError, ensure_user_profile


def resolve_profile_for_access(user):
    try:
        return ensure_user_profile(user, source_user_id=str(user.id), check_number=user.username)
    except ProfileConflictError:
        return None


def validate_access_delivery_target(
    user,
    *,
    missing_email_message: str,
    archived_message: str,
):
    profile = resolve_profile_for_access(user)
    if not user.email:
        return profile, missing_email_message
    if profile and profile.status == "Archived":
        return profile, archived_message
    return profile, ""


def mark_account_email(profile, *, delivery_status: str, error_message: str = ""):
    if not profile:
        return
    profile.accountEmailStatus = delivery_status
    profile.accountEmailSentAt = timezone.now() if delivery_status == "sent" else None
    profile.accountEmailError = "" if delivery_status != "failed" else error_message
    profile.save(update_fields=["accountEmailStatus", "accountEmailSentAt", "accountEmailError"])


def deliver_temporary_password(
    user,
    *,
    reason: str,
    password: str | None = None,
    missing_email_message: str,
    archived_message: str,
) -> tuple[bool, str, str]:
    profile, validation_error = validate_access_delivery_target(
        user,
        missing_email_message=missing_email_message,
        archived_message=archived_message,
    )
    if validation_error:
        return False, validation_error, ""

    temporary_password = password or secrets.token_urlsafe(10)

    with transaction.atomic():
        user.set_password(temporary_password)
        user.save(update_fields=["password"])

        if profile:
            profile.mustChangePassword = True
            profile.save(update_fields=["mustChangePassword"])

        delivery_status, message = send_temporary_password_email(user, temporary_password, reason=reason)
        mark_account_email(profile, delivery_status=delivery_status, error_message=message)
        if delivery_status == "failed":
            transaction.set_rollback(True)
            return False, message or "Failed to deliver the temporary password email.", temporary_password

    # "sent" and "queued" both mean the password change stands: a queued
    # message is guaranteed eventual delivery by the Core Gateway once the
    # notification service is back online, so there is no need to roll back.
    return True, message, temporary_password
