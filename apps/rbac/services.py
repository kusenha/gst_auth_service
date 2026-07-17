from apps.rbac.models import Role, RolePermission, UserPermission, UserServiceAccess


def resolve_service_keys(user) -> list[str]:
    """The service/app names (e.g. 'eda-service') this user has been explicitly
    granted access to. This is independent of role/permissions: a user can hold
    every permission a service defines and still be denied the app itself."""
    return sorted(UserServiceAccess.objects.filter(user=user).values_list("service__name", flat=True))


def resolve_permission_keys(user) -> list[str]:
    """Union of the user's role-derived permissions (via profile.role) and any direct
    per-user grants. Prefers a global role (service is null) over a same-keyed
    service-scoped role, since profile.role carries no service context of its own."""
    profile = getattr(user, "profile", None)
    role_key = profile.role if profile and profile.role else ""

    keys: set[str] = set()
    if role_key:
        role = (
            Role.objects.filter(key=role_key, service__isnull=True).first()
            or Role.objects.filter(key=role_key).first()
        )
        if role:
            keys.update(RolePermission.objects.filter(role=role).values_list("permission__key", flat=True))

    keys.update(UserPermission.objects.filter(user=user).values_list("permission__key", flat=True))
    return sorted(keys)
