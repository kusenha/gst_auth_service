from rest_framework import serializers

from apps.identity.models import UserProfile
from apps.rbac.models import Permission, Role, RolePermission, Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "displayName", "description", "isActive", "createdAt", "lastSeenAt"]
        read_only_fields = fields


class PermissionSerializer(serializers.ModelSerializer):
    codename = serializers.CharField(source="key", read_only=True)
    appLabel = serializers.CharField(source="service", read_only=True)

    class Meta:
        model = Permission
        fields = ["id", "service", "key", "codename", "name", "description", "appLabel", "createdAt"]
        read_only_fields = fields


class PermissionWriteSerializer(serializers.Serializer):
    service = serializers.CharField(max_length=80)
    key = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class RoleSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source="key", read_only=True)
    label = serializers.CharField(source="name", read_only=True)
    permissionKeys = serializers.SerializerMethodField()
    userCount = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "service", "value", "label", "permissionKeys", "userCount", "isSystem", "updatedAt"]
        read_only_fields = fields

    def get_permissionKeys(self, obj: Role) -> list[str]:
        return sorted(RolePermission.objects.filter(role=obj).values_list("permission__key", flat=True))

    def get_userCount(self, obj: Role) -> int:
        return UserProfile.objects.filter(role=obj.key).count()


class RoleWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    permissions = serializers.ListField(child=serializers.CharField(), required=False)
    service = serializers.CharField(max_length=80, required=False, allow_blank=True, default="")
