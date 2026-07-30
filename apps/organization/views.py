from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.models import UserProfile
from apps.organization.models import OrganisationalUnit, OrganisationalUnitHead
from apps.organization.serializers import (
    OrganisationalUnitHeadSerializer,
    OrganisationalUnitSerializer,
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


def _can_read(request) -> bool:
    # Read access is broad on purpose: any authenticated user, or any
    # internal service-to-service call (claim-request-service resolving an
    # approver has no per-user session of its own to authenticate with).
    if _is_internal_request(request):
        return True
    return bool(request.user and request.user.is_authenticated)


def _can_manage(request) -> bool:
    if _is_internal_request(request):
        return True
    if not request.user or not request.user.is_authenticated:
        return False
    return _request_role(request) in MANAGE_ROLES


def _employee_summary(employee_id: str) -> dict:
    profile = UserProfile.objects.filter(sourceUserId=employee_id).select_related("user").first()
    if not profile:
        return {"employeeId": employee_id, "employeeName": "", "employeeDesignation": ""}
    full_name = f"{profile.user.first_name} {profile.user.last_name}".strip()
    return {
        "employeeId": employee_id,
        "employeeName": full_name,
        "employeeDesignation": profile.designationName,
    }


class OrganisationalUnitListCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not _can_read(request):
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        queryset = OrganisationalUnit.objects.filter(isActive=True)
        parent_id = request.query_params.get("parent")
        if parent_id is not None:
            queryset = queryset.filter(parent_id=parent_id or None)
        return Response(OrganisationalUnitSerializer(queryset, many=True).data)

    def post(self, request):
        if not _can_manage(request):
            return Response(
                {"detail": "You do not have permission to create organisational units."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = OrganisationalUnitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrganisationalUnitDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, pk: int):
        if not _can_manage(request):
            return Response(
                {"detail": "You do not have permission to update organisational units."},
                status=status.HTTP_403_FORBIDDEN,
            )
        unit = OrganisationalUnit.objects.filter(pk=pk).first()
        if not unit:
            return Response({"detail": "Organisational unit not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrganisationalUnitSerializer(unit, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk: int):
        if not _can_manage(request):
            return Response(
                {"detail": "You do not have permission to delete organisational units."},
                status=status.HTTP_403_FORBIDDEN,
            )
        unit = OrganisationalUnit.objects.filter(pk=pk).first()
        if not unit:
            return Response({"detail": "Organisational unit not found."}, status=status.HTTP_404_NOT_FOUND)
        unit.isActive = False
        unit.save(update_fields=["isActive"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganisationalUnitHeadListCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not _can_read(request):
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        queryset = OrganisationalUnitHead.objects.filter(isActive=True)
        unit_id = request.query_params.get("organisationalUnit")
        if unit_id is not None:
            queryset = queryset.filter(organisationalUnit_id=unit_id)
        return Response(OrganisationalUnitHeadSerializer(queryset, many=True).data)

    def post(self, request):
        if not _can_manage(request):
            return Response(
                {"detail": "You do not have permission to assign organisational unit heads."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = OrganisationalUnitHeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrganisationalUnitHeadDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, pk: int):
        if not _can_manage(request):
            return Response(
                {"detail": "You do not have permission to update organisational unit heads."},
                status=status.HTTP_403_FORBIDDEN,
            )
        head = OrganisationalUnitHead.objects.filter(pk=pk).first()
        if not head:
            return Response({"detail": "Organisational unit head not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrganisationalUnitHeadSerializer(head, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk: int):
        if not _can_manage(request):
            return Response(
                {"detail": "You do not have permission to remove organisational unit heads."},
                status=status.HTTP_403_FORBIDDEN,
            )
        head = OrganisationalUnitHead.objects.filter(pk=pk).first()
        if not head:
            return Response({"detail": "Organisational unit head not found."}, status=status.HTTP_404_NOT_FOUND)
        head.isActive = False
        head.save(update_fields=["isActive"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUnitHeadView(APIView):
    """The single query every consuming service's workflow-approver
    resolution actually needs: who currently, effectively heads this unit.
    Centralized here rather than reimplemented per consuming service."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, pk: int):
        if not _can_read(request):
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        unit = OrganisationalUnit.objects.filter(pk=pk, isActive=True).first()
        if not unit:
            return Response({"detail": "Organisational unit not found."}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()
        candidates = OrganisationalUnitHead.objects.filter(
            organisationalUnit=unit,
            isActive=True,
            effectiveFrom__lte=today,
        ).filter(Q(effectiveTo__isnull=True) | Q(effectiveTo__gte=today))

        # A confirmed (non-acting) head takes precedence over an acting one
        # if both happen to be effective at once; fall back to the acting
        # head only when there's no confirmed head currently in post.
        head = (
            candidates.filter(isActing=False).order_by("-effectiveFrom").first()
            or candidates.filter(isActing=True).order_by("-effectiveFrom").first()
        )
        if not head:
            return Response(
                {"detail": f"No current head is configured for organisational unit '{unit.name}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = {
            "organisationalUnitId": unit.pk,
            "organisationalUnitName": unit.name,
            "leadershipRole": head.leadershipRole,
            "isActing": head.isActing,
            "effectiveFrom": head.effectiveFrom,
            "effectiveTo": head.effectiveTo,
            **_employee_summary(head.employeeId),
        }
        return Response(payload)
