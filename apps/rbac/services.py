from apps.identity.models import UserProfile
from apps.rbac.models import Role, RolePermission, Service, UserPermission, UserServiceAccess

ADMIN_ROLES = {"administrator", "super_admin"}


def grant_service_access_to_admins(service: Service, granted_by: str) -> int:
    """Every administrator/super_admin account gets access to `service`
    without a human granting it by hand on the App Access screen. Called
    both when a service self-registers (InternalRbacRegisterView) and on
    every auth-service startup (sync_admin_access), since not every service
    calls the registration endpoint."""
    admin_user_ids = UserProfile.objects.filter(role__in=ADMIN_ROLES).values_list("user_id", flat=True)
    existing_ids = set(
        UserServiceAccess.objects.filter(service=service, user_id__in=admin_user_ids).values_list(
            "user_id", flat=True
        )
    )
    created = UserServiceAccess.objects.bulk_create(
        [
            UserServiceAccess(user_id=uid, service=service, grantedBy=granted_by)
            for uid in admin_user_ids
            if uid not in existing_ids
        ]
    )
    return len(created)


def resolve_service_keys(user) -> list[str]:
    """The service/app names (e.g. 'eda-service') this user has been explicitly
    granted access to. This is independent of role/permissions: a user can hold
    every permission a service defines and still be denied the app itself."""
    return sorted(UserServiceAccess.objects.filter(user=user).values_list("service__name", flat=True))


def resolve_permission_keys(user) -> list[str]:
    """Union of the user's role-derived permissions (via profile.role) and any direct
    per-user grants. profile.role is a single account-wide name (e.g.
    "administrator"), but each service registers its own Role row scoped to
    itself under that same key (see InternalRbacRegisterView) — a user gets
    the union of whatever every service has granted that role name, not just
    one service's definition of it."""
    profile = getattr(user, "profile", None)
    role_key = profile.role if profile and profile.role else ""

    keys: set[str] = set()
    if role_key:
        role_ids = Role.objects.filter(key=role_key).values_list("id", flat=True)
        keys.update(
            RolePermission.objects.filter(role_id__in=role_ids).values_list("permission__key", flat=True)
        )

    keys.update(UserPermission.objects.filter(user=user).values_list("permission__key", flat=True))
    return sorted(keys)
