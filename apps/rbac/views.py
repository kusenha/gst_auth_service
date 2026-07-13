import re

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rbac.models import Permission, Role, RolePermission, Service
from apps.rbac.serializers import (
    PermissionSerializer,
    PermissionWriteSerializer,
    RoleSerializer,
    RoleWriteSerializer,
    ServiceSerializer,
)

MANAGE_ROLES = {"hr_officer", "administrator", "super_admin"}


def _is_internal_request(request) -> bool:
    token = getattr(settings, "AUTH_INTERNAL_TOKEN", "")
    if not token:
        return False
    return request.headers.get("X-Internal-Token", "") == token


def _request_role(request) -> str:
    profile = getattr(request.user, "profile", None)
    if profile and profile.role:
        return profile.role
    roles = list(request.user.groups.values_list("name", flat=True))
    return roles[0] if roles else "employee"


def _can_manage_rbac(request) -> bool:
    if _is_internal_request(request):
        return True
    if not request.user or not request.user.is_authenticated:
        return False
    return _request_role(request) in MANAGE_ROLES


def _slugify_key(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "role"


def _sync_role_permissions(role: Role, permission_keys: list[str]) -> None:
    matched = Permission.objects.filter(key__in=permission_keys)
    if role.service:
        matched = matched.filter(service=role.service)
    matched_ids = set(matched.values_list("id", flat=True))

    RolePermission.objects.filter(role=role).exclude(permission_id__in=matched_ids).delete()
    existing_ids = set(RolePermission.objects.filter(role=role).values_list("permission_id", flat=True))
    RolePermission.objects.bulk_create(
        [RolePermission(role=role, permission_id=pid) for pid in matched_ids - existing_ids]
    )


class ServiceListView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        if not _can_manage_rbac(request):
            return Response({"detail": "You do not have permission to list services."}, status=status.HTTP_403_FORBIDDEN)
        return Response(ServiceSerializer(Service.objects.all(), many=True).data)


class RoleListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        if not _can_manage_rbac(request):
            return Response({"detail": "You do not have permission to list roles."}, status=status.HTTP_403_FORBIDDEN)
        queryset = Role.objects.all()
        service = request.query_params.get("service")
        if service is not None:
            queryset = queryset.filter(service=service)
        return Response(RoleSerializer(queryset, many=True).data)

    def post(self, request):
        if not _can_manage_rbac(request):
            return Response({"detail": "You do not have permission to create roles."}, status=status.HTTP_403_FORBIDDEN)
        serializer = RoleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        name = data.get("name", "").strip()
        if not name:
            return Response({"detail": "name is required."}, status=status.HTTP_400_BAD_REQUEST)

        service = data.get("service", "")
        key = _slugify_key(name)
        if Role.objects.filter(service=service, key=key).exists():
            return Response(
                {"detail": f"A role with key '{key}' already exists for this service."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        role = Role.objects.create(service=service, key=key, name=name)
        _sync_role_permissions(role, data.get("permissions", []))
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def patch(self, request, pk: int):
        if not _can_manage_rbac(request):
            return Response({"detail": "You do not have permission to update roles."}, status=status.HTTP_403_FORBIDDEN)
        role = Role.objects.filter(pk=pk).first()
        if not role:
            return Response({"detail": "Role not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RoleWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        name = data.get("name")
        if name is not None and name.strip():
            role.name = name.strip()
            role.save(update_fields=["name"])
        if "permissions" in data:
            _sync_role_permissions(role, data["permissions"])
        return Response(RoleSerializer(role).data)

    def delete(self, request, pk: int):
        if not _can_manage_rbac(request):
            return Response({"detail": "You do not have permission to delete roles."}, status=status.HTTP_403_FORBIDDEN)
        role = Role.objects.filter(pk=pk).first()
        if not role:
            return Response({"detail": "Role not found."}, status=status.HTTP_404_NOT_FOUND)
        if role.isSystem:
            return Response(
                {"detail": "This role is protected by the system and cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PermissionListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        if not _can_manage_rbac(request):
            return Response({"detail": "You do not have permission to list permissions."}, status=status.HTTP_403_FORBIDDEN)
        queryset = Permission.objects.all()
        service = request.query_params.get("service")
        if service is not None:
            queryset = queryset.filter(service=service)
        return Response(PermissionSerializer(queryset, many=True).data)

    def post(self, request):
        if not _can_manage_rbac(request):
            return Response({"detail": "You do not have permission to create permissions."}, status=status.HTTP_403_FORBIDDEN)
        serializer = PermissionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        permission, created = Permission.objects.get_or_create(
            service=data["service"].strip().lower(),
            key=data["key"].strip(),
            defaults={"name": data.get("name") or data["key"], "description": data.get("description", "")},
        )
        if not created:
            return Response(
                {"detail": "A permission with this key already exists for this service."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(PermissionSerializer(permission).data, status=status.HTTP_201_CREATED)


class PermissionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def patch(self, request, pk: int):
        if not _can_manage_rbac(request):
            return Response({"detail": "You do not have permission to update permissions."}, status=status.HTTP_403_FORBIDDEN)
        permission = Permission.objects.filter(pk=pk).first()
        if not permission:
            return Response({"detail": "Permission not found."}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name")
        description = request.data.get("description")
        update_fields = []
        if name is not None:
            permission.name = name
            update_fields.append("name")
        if description is not None:
            permission.description = description
            update_fields.append("description")
        if update_fields:
            permission.save(update_fields=update_fields)
        return Response(PermissionSerializer(permission).data)

    def delete(self, request, pk: int):
        if not _can_manage_rbac(request):
            return Response({"detail": "You do not have permission to delete permissions."}, status=status.HTTP_403_FORBIDDEN)
        permission = Permission.objects.filter(pk=pk).first()
        if not permission:
            return Response({"detail": "Permission not found."}, status=status.HTTP_404_NOT_FOUND)
        permission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InternalRbacRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not _is_internal_request(request):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        service_name = str(request.data.get("service", "")).strip().lower()
        if not service_name:
            return Response({"detail": "service is required."}, status=status.HTTP_400_BAD_REQUEST)

        service = Service.touch(service_name)

        permissions_created = 0
        permissions_updated = 0
        for item in request.data.get("permissions") or []:
            key = str(item.get("key", "")).strip()
            if not key:
                continue
            _, created = Permission.objects.update_or_create(
                service=service.name,
                key=key,
                defaults={"name": item.get("name") or key, "description": item.get("description", "")},
            )
            if created:
                permissions_created += 1
            else:
                permissions_updated += 1

        roles_created = 0
        for item in request.data.get("roles") or []:
            key = str(item.get("key", "")).strip()
            if not key:
                continue
            role_service = str(item.get("service", service.name)).strip().lower()
            if Role.objects.filter(service=role_service, key=key).exists():
                continue
            role = Role.objects.create(
                service=role_service,
                key=key,
                name=item.get("name") or key,
                isSystem=bool(item.get("isSystem", False)),
            )
            _sync_role_permissions(role, item.get("permissionKeys") or [])
            roles_created += 1

        return Response(
            {
                "service": service.name,
                "permissionsCreated": permissions_created,
                "permissionsUpdated": permissions_updated,
                "rolesCreated": roles_created,
            }
        )
