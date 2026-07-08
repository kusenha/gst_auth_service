from django.contrib import admin

from apps.identity.models import RefreshTokenAudit, ServiceClient

admin.site.register(ServiceClient)
admin.site.register(RefreshTokenAudit)
