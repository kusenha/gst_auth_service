from rest_framework import serializers

from apps.identity.models import UserProfile
from apps.rbac.models import Permission, Role, RolePermission, Service, UserServiceAccess


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "displayName",
            "description",
            "isActive",
            "createdAt",
            "lastSeenAt",
            "showInLauncher",
            "frontendUrl",
            "icon",
            "color",
            "sortOrder",
        ]
        read_only_fields = ["id", "createdAt", "lastSeenAt"]


class LauncherAppSerializer(serializers.ModelSerializer):
    hasAccess = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ["id", "name", "displayName", "description", "frontendUrl", "icon", "color", "hasAccess"]
        read_only_fields = fields

    def get_hasAccess(self, obj: Service) -> bool:
        granted_names: set[str] = self.context.get("granted_names", set())
        return obj.name in granted_names


class AssignServicesSerializer(serializers.Serializer):
    services = serializers.ListField(child=serializers.CharField(), allow_empty=True)


class PermissionSerializer(serializers.ModelSerializer):
    codename = serializers.CharField(source="key", read_only=True)
    appLabel = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ["id", "key", "codename", "name", "description", "appLabel", "createdAt"]
        read_only_fields = fields

    def get_appLabel(self, obj: Permission) -> str:
        # Permissions carry no service of their own; group them for display
        # purposes by the domain prefix of their key (e.g. "requests.create"
        # groups under "requests").
        return obj.key.split(".", 1)[0] if "." in obj.key else "general"


class PermissionWriteSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class RoleSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source="key", read_only=True)
    label = serializers.CharField(source="name", read_only=True)
    service = serializers.SerializerMethodField()
    serviceId = serializers.IntegerField(source="service_id", read_only=True)
    permissionKeys = serializers.SerializerMethodField()
    userCount = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id",
            "service",
            "serviceId",
            "value",
            "label",
            "permissionKeys",
            "userCount",
            "isSystem",
            "updatedAt",
        ]
        read_only_fields = fields

    def get_service(self, obj: Role) -> str:
        return obj.service.name if obj.service_id else ""

    def get_permissionKeys(self, obj: Role) -> list[str]:
        return sorted(RolePermission.objects.filter(role=obj).values_list("permission__key", flat=True))

    def get_userCount(self, obj: Role) -> int:
        return UserProfile.objects.filter(role=obj.key).count()


class RoleWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    permissions = serializers.ListField(child=serializers.CharField(), required=False)
    service = serializers.CharField(max_length=80, required=False, allow_blank=True, default="")
