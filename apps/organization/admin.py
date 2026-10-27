from django.contrib import admin

from apps.organization.models import Department, Designation, OrganisationalUnit, OrganisationalUnitHead

admin.site.register(Department)
admin.site.register(Designation)

admin.site.register(OrganisationalUnit)
admin.site.register(OrganisationalUnitHead)
