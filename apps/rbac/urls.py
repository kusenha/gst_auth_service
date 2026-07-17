from django.urls import path

from apps.rbac.views import (
    InternalRbacRegisterView,
    LauncherAppsView,
    PermissionDetailView,
    PermissionListCreateView,
    RoleDetailView,
    RoleListCreateView,
    ServiceListView,
)

urlpatterns = [
    path("services/", ServiceListView.as_view(), name="rbac-services"),
    path("apps/", LauncherAppsView.as_view(), name="rbac-apps"),
    path("roles/", RoleListCreateView.as_view(), name="rbac-roles"),
    path("roles/<int:pk>/", RoleDetailView.as_view(), name="rbac-role-detail"),
    path("permissions/", PermissionListCreateView.as_view(), name="rbac-permissions"),
    path("permissions/<int:pk>/", PermissionDetailView.as_view(), name="rbac-permission-detail"),
    path("internal/rbac/register/", InternalRbacRegisterView.as_view(), name="rbac-internal-register"),
]
