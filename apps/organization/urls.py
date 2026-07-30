from django.urls import path

from apps.organization.views import (
    CurrentUnitHeadView,
    OrganisationalUnitDetailView,
    OrganisationalUnitHeadDetailView,
    OrganisationalUnitHeadListCreateView,
    OrganisationalUnitListCreateView,
)

urlpatterns = [
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
