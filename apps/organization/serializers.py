import uuid

from rest_framework import serializers

from apps.identity.models import UserProfile
from apps.organization.models import Department, Designation, OrganisationalUnit, OrganisationalUnitHead


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


class DepartmentSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False, max_length=50)
    employeeCount = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "name", "headId", "description", "employeeCount"]

    def get_employeeCount(self, obj) -> int:
        return self.context.get("employee_counts", {}).get(obj.id, 0)

    def validate_id(self, value):
        if self.instance is not None and value != self.instance.id:
            raise serializers.ValidationError("A department's id cannot be changed.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        department_id = attrs.get("id") or getattr(self.instance, "id", None)
        head_id = attrs.get("headId", getattr(self.instance, "headId", ""))

        if not head_id:
            if self.instance is not None and "headId" in attrs:
                raise serializers.ValidationError({"headId": "Every department must have a department head."})
            return attrs

        head = UserProfile.objects.filter(sourceUserId=str(head_id)).first()
        if not head:
            raise serializers.ValidationError({"headId": "Selected department head does not exist."})
        if department_id and str(head.departmentId) != str(department_id):
            raise serializers.ValidationError({"headId": "Selected head must belong to the same department."})
        return attrs

    def create(self, validated_data):
        validated_data.setdefault("id", f"d-{uuid.uuid4().hex[:10]}")
        return super().create(validated_data)


class DesignationSerializer(serializers.ModelSerializer):
    departmentId = serializers.PrimaryKeyRelatedField(
        source="department", queryset=Department.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = Designation
        fields = ["id", "name", "departmentId"]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Designation.objects.all(),
                fields=["departmentId", "name"],
                message="This department already has a designation with that name.",
            )
        ]
