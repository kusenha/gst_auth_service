from django.urls import path

from apps.identity.views import (
    LoginView,
    LogoutView,
    RefreshView,
    RegisterView,
    ResetUserPasswordView,
    ResendAccountEmailView,
    SsoSessionView,
    UserDetailView,
    UserListCreateView,
    UserPermissionsView,
    UserRoleView,
    UserServiceAccessView,
    UserStatusView,
    change_password,
    change_temporary_password,
    me,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("sso/session/", SsoSessionView.as_view(), name="sso-session"),
    path("me/", me, name="me"),
    path("change-password/", change_password, name="change-password"),
    path("change-temporary-password/", change_temporary_password, name="change-temporary-password"),
    path("users/", UserListCreateView.as_view(), name="users"),
    path("users/<str:user_ref>/", UserDetailView.as_view(), name="user-detail"),
    path("users/<str:user_ref>/reset-password/", ResetUserPasswordView.as_view(), name="user-reset-password"),
    path("users/<str:user_ref>/resend-account-email/", ResendAccountEmailView.as_view(), name="user-resend-account-email"),
    path("users/<str:user_ref>/set-status/", UserStatusView.as_view(), name="user-set-status"),
    path("users/<str:user_ref>/assign-role/", UserRoleView.as_view(), name="user-assign-role"),
    path("users/<str:user_ref>/assign-permissions/", UserPermissionsView.as_view(), name="user-assign-permissions"),
    path("users/<str:user_ref>/assign-services/", UserServiceAccessView.as_view(), name="user-assign-services"),
]
