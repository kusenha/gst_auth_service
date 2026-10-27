from django.urls import path

from apps.organization.views import (
    CurrentUnitHeadView,
    DepartmentDetailView,
    DepartmentListCreateView,
    DesignationDetailView,
    DesignationListCreateView,
    OrganisationalUnitDetailView,
    OrganisationalUnitHeadDetailView,
    OrganisationalUnitHeadListCreateView,
    OrganisationalUnitListCreateView,
)

urlpatterns = [
    path("departments/", DepartmentListCreateView.as_view(), name="organization-departments"),
    path("departments/<str:pk>/", DepartmentDetailView.as_view(), name="organization-department-detail"),
    path("designations/", DesignationListCreateView.as_view(), name="organization-designations"),
    path("designations/<int:pk>/", DesignationDetailView.as_view(), name="organization-designation-detail"),
    path("units/", OrganisationalUnitListCreateView.as_view(), name="organization-units"),
    path("units/<int:pk>/", OrganisationalUnitDetailView.as_view(), name="organization-unit-detail"),
    path("units/<int:pk>/current-head/", CurrentUnitHeadView.as_view(), name="organization-unit-current-head"),
    path("unit-heads/", OrganisationalUnitHeadListCreateView.as_view(), name="organization-unit-heads"),
    path(
        "unit-heads/<int:pk>/",
        OrganisationalUnitHeadDetailView.as_view(),
        name="organization-unit-head-detail",
    ),
]
