from django.contrib import admin

from apps.organization.models import OrganisationalUnit, OrganisationalUnitHead

admin.site.register(OrganisationalUnit)
admin.site.register(OrganisationalUnitHead)
