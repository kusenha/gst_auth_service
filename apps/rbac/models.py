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

    class Meta:
        ordering = ["name"]

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
    service = models.CharField(
        max_length=80,
        blank=True,
        db_index=True,
        help_text="Blank = a global role usable by any service (e.g. super_admin).",
    )
    key = models.CharField(max_length=80, db_index=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    isSystem = models.BooleanField(default=False, help_text="System roles cannot be deleted.")
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["service", "key"]
        constraints = [
            models.UniqueConstraint(fields=["service", "key"], name="unique_service_role_key"),
        ]

    def __str__(self) -> str:
        return f"{self.service or 'global'}:{self.key}"


class Permission(models.Model):
    service = models.CharField(max_length=80, db_index=True)
    key = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["service", "key"]
        constraints = [
            models.UniqueConstraint(fields=["service", "key"], name="unique_service_permission_key"),
        ]

    def __str__(self) -> str:
        return f"{self.service}:{self.key}"


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
