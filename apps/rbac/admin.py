from django.contrib import admin

from apps.rbac.models import Permission, Role, RolePermission, Service, UserPermission

admin.site.register(Service)
admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(RolePermission)
admin.site.register(UserPermission)
