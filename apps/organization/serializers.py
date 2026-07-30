from rest_framework import serializers

from apps.organization.models import OrganisationalUnit, OrganisationalUnitHead


class OrganisationalUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationalUnit
        fields = ["id", "name", "unitType", "parent", "isActive", "createdAt"]


class OrganisationalUnitHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationalUnitHead
        fields = [
            "id",
            "organisationalUnit",
            "employeeId",
            "leadershipRole",
            "isActing",
            "effectiveFrom",
            "effectiveTo",
            "isActive",
            "createdAt",
        ]
