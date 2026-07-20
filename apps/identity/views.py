import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.identity.serializers import (
    AdminResetPasswordSerializer,
    AdminUserWriteSerializer,
    AssignPermissionsSerializer,
    AssignRoleSerializer,
    AuthTokenSerializer,
    ChangePasswordSerializer,
    MeUpdateSerializer,
    RegisterSerializer,
    SetUserStatusSerializer,
    TemporaryPasswordChangeSerializer,
    UserSerializer,
)
from apps.identity.services.access_delivery import (
    deliver_temporary_password,
)
from apps.identity.services.profiles import ensure_user_profile

User = get_user_model()


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


def _can_manage_users(request) -> bool:
    if _is_internal_request(request):
        return True
    if not request.user or not request.user.is_authenticated:
        return False
    return _request_role(request) in {"hr_officer", "administrator", "super_admin"}


def _resolve_user(user_ref: str):
    user = User.objects.filter(profile__sourceUserId=user_ref).select_related("profile").first()
    if user:
        return user

    if user_ref.isdigit():
        user = User.objects.filter(id=int(user_ref)).select_related("profile").first()
        if user:
            return user

    return User.objects.filter(Q(username__iexact=user_ref) | Q(email__iexact=user_ref)).select_related("profile").first()


def _ensure_profile(user):
    return ensure_user_profile(user, source_user_id=str(user.id), check_number=user.username)


def _set_sso_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        settings.SSO_COOKIE_NAME,
        refresh_token,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.SSO_COOKIE_SECURE,
        samesite="Lax",
        domain=settings.SSO_COOKIE_DOMAIN,
        path="/api/auth/",
    )


def _clear_sso_cookie(response: Response) -> None:
    response.delete_cookie(settings.SSO_COOKIE_NAME, path="/api/auth/", domain=settings.SSO_COOKIE_DOMAIN)


class LoginView(TokenObtainPairView):
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh = response.data.get("refresh") if isinstance(response.data, dict) else None
        if refresh:
            _set_sso_cookie(response, refresh)
        return response


class RefreshView(TokenRefreshView):
    pass


class SsoSessionView(APIView):
    """Silent single-sign-on check: if the browser is carrying a valid SSO
    session cookie (set by a login in any GST EDA app), returns a fresh
    access/refresh pair for THIS app without requiring the user to fill in
    the login form again."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw = request.COOKIES.get(settings.SSO_COOKIE_NAME)
        if not raw:
            return Response({"detail": "No active session."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            existing = RefreshToken(raw)
        except TokenError:
            response = Response({"detail": "Session expired."}, status=status.HTTP_401_UNAUTHORIZED)
            _clear_sso_cookie(response)
            return response

        user = User.objects.filter(pk=existing["user_id"]).select_related("profile").first()
        if not user or not user.is_active:
            response = Response({"detail": "Session is no longer valid."}, status=status.HTTP_401_UNAUTHORIZED)
            _clear_sso_cookie(response)
            return response
        profile = getattr(user, "profile", None)
        if profile and profile.status == "Archived":
            response = Response({"detail": "Session is no longer valid."}, status=status.HTTP_401_UNAUTHORIZED)
            _clear_sso_cookie(response)
            return response
        if profile and profile.tokensInvalidBefore and existing["iat"] < int(profile.tokensInvalidBefore.timestamp()):
            # Cookie predates the last logout (e.g. a copy that outlived the
            # one already cleared in the browser that logged out).
            response = Response({"detail": "Session is no longer valid."}, status=status.HTTP_401_UNAUTHORIZED)
            _clear_sso_cookie(response)
            return response

        refresh = AuthTokenSerializer.get_token(user)
        response = Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )
        _set_sso_cookie(response, str(refresh))
        return response


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # The SSO cookie (not the Authorization header, which may already be
        # stale or absent) is the reliable identity carrier for "whose
        # session is this" — mirrors how SsoSessionView resolves the user.
        raw = request.COOKIES.get(settings.SSO_COOKIE_NAME)
        if raw:
            try:
                existing = RefreshToken(raw)
                user = User.objects.filter(pk=existing["user_id"]).select_related("profile").first()
            except TokenError:
                user = None
            if user:
                profile = _ensure_profile(user)
                if profile:
                    profile.tokensInvalidBefore = timezone.now()
                    profile.save(update_fields=["tokensInvalidBefore"])

        response = Response({"ok": True})
        _clear_sso_cookie(response)
        return response


class RegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not _can_manage_users(request):
            return Response({"detail": "You do not have permission to create users."}, status=status.HTTP_403_FORBIDDEN)
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    if request.method == "PATCH":
        serializer = MeUpdateSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"ok": True}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def change_temporary_password(request):
    serializer = TemporaryPasswordChangeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"ok": True}, status=status.HTTP_200_OK)


class UserListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        if not _can_manage_users(request):
            return Response({"detail": "You do not have permission to manage users."}, status=status.HTTP_403_FORBIDDEN)

        queryset = User.objects.select_related("profile").all().order_by("id")

        source_user_id = request.query_params.get("id")
        check_number = request.query_params.get("checkNumber")
        role = request.query_params.get("role")
        status_value = request.query_params.get("status")
        department_id = request.query_params.get("departmentId")
        designation_id = request.query_params.get("designationId")
        designation_name = request.query_params.get("designation")

        if source_user_id:
            queryset = queryset.filter(profile__sourceUserId=str(source_user_id))
        if check_number:
            queryset = queryset.filter(profile__checkNumber__iexact=check_number)
        if role:
            queryset = queryset.filter(profile__role=role)
        if status_value:
            queryset = queryset.filter(profile__status=status_value)
        if department_id:
            queryset = queryset.filter(profile__departmentId=department_id)
        if designation_id:
            try:
                designation_id_int = int(designation_id)
            except ValueError:
                designation_id_int = None
            if designation_id_int is not None:
                queryset = queryset.filter(profile__designationId=designation_id_int)
        if designation_name:
            queryset = queryset.filter(profile__designationName__iexact=designation_name)

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(profile__middleName__icontains=search)
                | Q(profile__checkNumber__icontains=search)
                | Q(profile__personnelNumber__icontains=search)
                | Q(email__icontains=search)
                | Q(profile__designationName__icontains=search)
            )
            queryset = queryset[:20]

        return Response(UserSerializer(queryset, many=True).data)

    def post(self, request):
        if not _can_manage_users(request):
            return Response({"detail": "You do not have permission to manage users."}, status=status.HTTP_403_FORBIDDEN)
        serializer = AdminUserWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        generated_password = getattr(user, "_generated_password", None)
        if generated_password:
            deliver_temporary_password(
                user,
                reason="created",
                password=generated_password,
                missing_email_message="User email is required before sending account access.",
                archived_message="Archived employees must be reactivated before sending account access.",
            )
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, user_ref: str):
        if not _can_manage_users(request):
            return Response({"detail": "You do not have permission to manage users."}, status=status.HTTP_403_FORBIDDEN)
        user = _resolve_user(user_ref)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(user).data)

    def patch(self, request, user_ref: str):
        if not _can_manage_users(request):
            return Response({"detail": "You do not have permission to manage users."}, status=status.HTTP_403_FORBIDDEN)
        user = _resolve_user(user_ref)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUserWriteSerializer(instance=user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)

    def delete(self, request, user_ref: str):
        if not _can_manage_users(request):
            return Response({"detail": "You do not have permission to archive users."}, status=status.HTTP_403_FORBIDDEN)
        user = _resolve_user(user_ref)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        profile = _ensure_profile(user)
        if profile:
            profile.status = "Archived"
            profile.save(update_fields=["status"])

        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class ResetUserPasswordView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, user_ref: str):
        if not _can_manage_users(request):
            return Response({"detail": "You do not have permission to reset passwords."}, status=status.HTTP_403_FORBIDDEN)

        user = _resolve_user(user_ref)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data.get("newPassword") or secrets.token_urlsafe(10)
        ok, message, _ = deliver_temporary_password(
            user,
            reason="password_reset",
            password=new_password,
            missing_email_message="User email is required before sending a temporary password.",
            archived_message="Archived employees must be reactivated before resetting access.",
        )
        if not ok:
            status_code = (
                status.HTTP_400_BAD_REQUEST
                if message in {
                    "User email is required before sending a temporary password.",
                    "Archived employees must be reactivated before resetting access.",
                }
                else status.HTTP_502_BAD_GATEWAY
            )
            return Response({"detail": message or "Failed to send the temporary password email."}, status=status_code)

        response = {"ok": True, "user": UserSerializer(user).data}
        if message:
            response["message"] = message
        return Response(response)


class UserStatusView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, user_ref: str):
        if not _can_manage_users(request):
            return Response({"detail": "You do not have permission to update user status."}, status=status.HTTP_403_FORBIDDEN)

        user = _resolve_user(user_ref)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SetUserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = _ensure_profile(user)
        if profile:
            profile.status = serializer.validated_data["status"]
            profile.save(update_fields=["status"])
        user.is_active = serializer.validated_data["status"] != "Archived"
        user.save(update_fields=["is_active"])

        return Response(UserSerializer(user).data)


class ResendAccountEmailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, user_ref: str):
        if not _can_manage_users(request):
            return Response({"detail": "You do not have permission to resend account access."}, status=status.HTTP_403_FORBIDDEN)

        user = _resolve_user(user_ref)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        ok, message, _ = deliver_temporary_password(
            user,
            reason="created",
            missing_email_message="User email is required before sending account access.",
            archived_message="Archived employees must be reactivated before sending account access.",
        )
        if not ok:
            status_code = (
                status.HTTP_400_BAD_REQUEST
                if message in {
                    "User email is required before sending account access.",
                    "Archived employees must be reactivated before sending account access.",
                }
                else status.HTTP_502_BAD_GATEWAY
            )
            return Response({"detail": message or "Failed to send the account email."}, status=status_code)

        response = {"ok": True, "user": UserSerializer(user).data}
        if message:
            response["message"] = message
        return Response(response)


class UserRoleView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, user_ref: str):
        if not _can_manage_users(request):
            return Response({"detail": "You do not have permission to assign roles."}, status=status.HTTP_403_FORBIDDEN)

        user = _resolve_user(user_ref)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data["role"]

        group, _ = Group.objects.get_or_create(name=role)
        user.groups.set([group])

        profile = getattr(user, "profile", None)
        if profile:
            profile.role = role
            profile.save(update_fields=["role"])

        return Response(UserSerializer(user).data)


class UserPermissionsView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, user_ref: str):
        if not _can_manage_users(request):
            return Response(
                {"detail": "You do not have permission to assign permissions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = _resolve_user(user_ref)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssignPermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permission_ids = set(serializer.validated_data["permissions"])

        from apps.rbac.models import UserPermission

        UserPermission.objects.filter(user=user).exclude(permission_id__in=permission_ids).delete()
        existing_ids = set(UserPermission.objects.filter(user=user).values_list("permission_id", flat=True))
        UserPermission.objects.bulk_create(
            [UserPermission(user=user, permission_id=pid) for pid in permission_ids - existing_ids]
        )
        return Response(UserSerializer(user).data)


class UserServiceAccessView(APIView):
    """Grants or revokes which apps/services a user may open, independent of
    their role or permissions (e.g. an administrator who should not have
    Configuration app access)."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, user_ref: str):
        if not _can_manage_users(request):
            return Response(
                {"detail": "You do not have permission to assign app access."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = _resolve_user(user_ref)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        from apps.rbac.serializers import AssignServicesSerializer

        serializer = AssignServicesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service_names = {name.strip().lower() for name in serializer.validated_data["services"] if name.strip()}

        from apps.rbac.models import Service, UserServiceAccess

        service_ids = set(Service.objects.filter(name__in=service_names).values_list("id", flat=True))
        actor = getattr(request.user, "username", "") or str(getattr(request.user, "id", ""))

        UserServiceAccess.objects.filter(user=user).exclude(service_id__in=service_ids).delete()
        existing_ids = set(UserServiceAccess.objects.filter(user=user).values_list("service_id", flat=True))
        UserServiceAccess.objects.bulk_create(
            [
                UserServiceAccess(user=user, service_id=sid, grantedBy=actor)
                for sid in service_ids - existing_ids
            ]
        )
        return Response(UserSerializer(user).data)
