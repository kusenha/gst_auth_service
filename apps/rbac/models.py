from django.conf import settings
from django.db import models
from django.utils import timezone


class Service(models.Model):
    """A consumer of this registry. Rows are created automatically the first time a
    service registers its permission catalog — no code change here is needed to onboard
    a new service beyond having it call the internal registration endpoint."""

    name = models.SlugField(max_length=80, unique=True)
    displayName = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    isActive = models.BooleanField(default=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    lastSeenAt = models.DateTimeField(null=True, blank=True)

    # Frontend-application / launcher metadata. Blank frontendUrl means this
    # service has no user-facing app of its own and never appears in the
    # app launcher (e.g. a pure backend service that hasn't opted in).
    showInLauncher = models.BooleanField(default=False)
    frontendUrl = models.URLField(max_length=300, blank=True)
    icon = models.CharField(max_length=10, blank=True, help_text="An emoji shown on the app tile.")
    color = models.CharField(max_length=7, blank=True, help_text="Accent hex color for the app tile, e.g. #005A9C.")
    sortOrder = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sortOrder", "name"]

    def __str__(self) -> str:
        return self.name

    @classmethod
    def touch(cls, name: str, *, display_name: str = "") -> "Service":
        normalized = name.strip().lower()
        service, created = cls.objects.get_or_create(
            name=normalized,
            defaults={"displayName": display_name or normalized},
        )
        update_fields = ["lastSeenAt"]
        service.lastSeenAt = timezone.now()
        if not created and display_name and not service.displayName:
            service.displayName = display_name
            update_fields.append("displayName")
        service.save(update_fields=update_fields)
        return service


class Role(models.Model):
    service = models.ForeignKey(
        Service,
        related_name="roles",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Null = a global role usable by any service (e.g. super_admin).",
    )
    key = models.CharField(max_length=80, db_index=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    isSystem = models.BooleanField(default=False, help_text="System roles cannot be deleted.")
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["service__name", "key"]
        constraints = [
            models.UniqueConstraint(fields=["service", "key"], name="unique_service_role_key"),
        ]

    def __str__(self) -> str:
        return f"{self.service.name if self.service_id else 'global'}:{self.key}"


class Permission(models.Model):
    """A capability key. Permissions are a global, service-agnostic vocabulary —
    which service(s) a permission is relevant to is expressed by which Role(s)
    (each scoped to a Service) include it via RolePermission, not by a field
    on Permission itself."""

    key = models.CharField(max_length=100, db_index=True, unique=True)
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["key"]

    def __str__(self) -> str:
        return self.key


class RolePermission(models.Model):
    role = models.ForeignKey(Role, related_name="rolePermissions", on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, related_name="rolePermissions", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="unique_role_permission"),
        ]


class UserPermission(models.Model):
    """Direct per-user permission grants, independent of role."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="directPermissions", on_delete=models.CASCADE
    )
    permission = models.ForeignKey(Permission, related_name="userPermissions", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "permission"], name="unique_user_permission"),
        ]


class UserServiceAccess(models.Model):
    """Grants a user access to an application/service, independent of their
    role or permissions. A user with the 'administrator' role, for example,
    still cannot open the Configuration app unless explicitly granted access
    to the 'configuration-service' Service here."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="serviceAccess", on_delete=models.CASCADE
    )
    service = models.ForeignKey(Service, related_name="userGrants", on_delete=models.CASCADE)
    grantedAt = models.DateTimeField(auto_now_add=True)
    grantedBy = models.CharField(max_length=150, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "service"], name="unique_user_service_access"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.service.name}"
