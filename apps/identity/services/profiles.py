from __future__ import annotations

from apps.identity.models import UserProfile


class ProfileConflictError(ValueError):
    pass


def ensure_user_profile(user, *, source_user_id: str | None = None, check_number: str | None = None) -> UserProfile:
    profile = getattr(user, "profile", None)
    if profile:
        return profile

    resolved_source_user_id = (source_user_id or "").strip() or str(user.id)
    resolved_check_number = (check_number or "").strip() or user.username

    existing_profile = (
        UserProfile.objects.select_related("user").filter(sourceUserId=resolved_source_user_id).first()
        or UserProfile.objects.select_related("user").filter(checkNumber=resolved_check_number).first()
    )
    if existing_profile:
        if existing_profile.user_id != user.id:
            raise ProfileConflictError(
                "Profile identifiers are already linked to another user "
                f"(sourceUserId={resolved_source_user_id}, checkNumber={resolved_check_number})."
            )
        return existing_profile

    return UserProfile.objects.create(
        user=user,
        sourceUserId=resolved_source_user_id,
        checkNumber=resolved_check_number,
    )
