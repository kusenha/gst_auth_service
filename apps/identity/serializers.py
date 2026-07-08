from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.identity.models import UserProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    checkNumber = serializers.SerializerMethodField()
    personnelNumber = serializers.SerializerMethodField()
    firstName = serializers.SerializerMethodField()
    middleName = serializers.SerializerMethodField()
    lastName = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    departmentId = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    designationId = serializers.SerializerMethodField()
    education = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    salaryScale = serializers.SerializerMethodField()
    dutyStation = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    dateEmployed = serializers.SerializerMethodField()
    bank = serializers.SerializerMethodField()
    accountNumber = serializers.SerializerMethodField()
    taxNumber = serializers.SerializerMethodField()
    nida = serializers.SerializerMethodField()
    supervisorId = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    mustChangePassword = serializers.SerializerMethodField()
    accountEmailStatus = serializers.SerializerMethodField()
    accountEmailSentAt = serializers.SerializerMethodField()
    accountEmailError = serializers.SerializerMethodField()
    permissionKeys = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "checkNumber",
            "personnelNumber",
            "firstName",
            "middleName",
            "lastName",
            "gender",
            "phone",
            "email",
            "departmentId",
            "designation",
            "designationId",
            "education",
            "status",
            "salaryScale",
            "dutyStation",
            "region",
            "dateEmployed",
            "bank",
            "accountNumber",
            "taxNumber",
            "nida",
            "supervisorId",
            "photo",
            "role",
            "mustChangePassword",
            "accountEmailStatus",
            "accountEmailSentAt",
            "accountEmailError",
            "permissionKeys",
        ]

    @staticmethod
    def _profile(obj):
        return getattr(obj, "profile", None)

    def get_id(self, obj):
        profile = self._profile(obj)
        if profile and profile.sourceUserId:
            return profile.sourceUserId
        return str(obj.id)

    def get_checkNumber(self, obj):
        profile = self._profile(obj)
        return profile.checkNumber if profile else obj.username

    def get_personnelNumber(self, obj):
        profile = self._profile(obj)
        return profile.personnelNumber if profile else None

    def get_firstName(self, obj):
        return obj.first_name

    def get_middleName(self, obj):
        profile = self._profile(obj)
        return profile.middleName if profile else ""

    def get_lastName(self, obj):
        return obj.last_name

    def get_gender(self, obj):
        profile = self._profile(obj)
        return profile.gender if profile else "Male"

    def get_phone(self, obj):
        profile = self._profile(obj)
        return profile.phone if profile else ""

    def get_departmentId(self, obj):
        profile = self._profile(obj)
        return profile.departmentId if profile else ""

    def get_designation(self, obj):
        profile = self._profile(obj)
        if not profile:
            return ""
        return profile.designationName or (str(profile.designationId) if profile.designationId else "")

    def get_designationId(self, obj):
        profile = self._profile(obj)
        return profile.designationId if profile else None

    def get_education(self, obj):
        profile = self._profile(obj)
        return profile.education if profile else "Bachelor"

    def get_status(self, obj):
        profile = self._profile(obj)
        return profile.status if profile else "Active"

    def get_salaryScale(self, obj):
        profile = self._profile(obj)
        return profile.salaryScale if profile else ""

    def get_dutyStation(self, obj):
        profile = self._profile(obj)
        return profile.dutyStation if profile else ""

    def get_region(self, obj):
        profile = self._profile(obj)
        return profile.region if profile else ""

    def get_dateEmployed(self, obj):
        profile = self._profile(obj)
        if profile and profile.dateEmployed:
            return profile.dateEmployed.isoformat()
        return ""

    def get_bank(self, obj):
        profile = self._profile(obj)
        return profile.bank if profile else ""

    def get_accountNumber(self, obj):
        profile = self._profile(obj)
        return profile.accountNumber if profile else ""

    def get_taxNumber(self, obj):
        profile = self._profile(obj)
        return profile.taxNumber if profile else ""

    def get_nida(self, obj):
        profile = self._profile(obj)
        return profile.nida if profile else ""

    def get_supervisorId(self, obj):
        profile = self._profile(obj)
        return profile.supervisorId if profile else ""

    def get_photo(self, obj):
        profile = self._profile(obj)
        return profile.photo if profile else ""

    def get_role(self, obj):
        profile = self._profile(obj)
        if profile and profile.role:
            return profile.role
        roles = list(obj.groups.values_list("name", flat=True))
        return roles[0] if roles else "employee"

    def get_mustChangePassword(self, obj):
        profile = self._profile(obj)
        return bool(profile.mustChangePassword) if profile else False

    def get_accountEmailStatus(self, obj):
        profile = self._profile(obj)
        return profile.accountEmailStatus if profile else "not_sent"

    def get_accountEmailSentAt(self, obj):
        profile = self._profile(obj)
        return profile.accountEmailSentAt.isoformat() if profile and profile.accountEmailSentAt else None

    def get_accountEmailError(self, obj):
        profile = self._profile(obj)
        return profile.accountEmailError if profile else ""

    def get_permissionKeys(self, obj):
        perms = set(obj.user_permissions.values_list("content_type__app_label", "codename"))
        for group in obj.groups.all():
            perms.update(group.permissions.values_list("content_type__app_label", "codename"))
        return sorted(f"{app}.{code}" for app, code in perms)


class MeUpdateSerializer(serializers.Serializer):
    firstName = serializers.CharField(required=False)
    middleName = serializers.CharField(required=False, allow_blank=True)
    lastName = serializers.CharField(required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    photo = serializers.URLField(required=False, allow_blank=True)
    dutyStation = serializers.CharField(required=False, allow_blank=True)
    bank = serializers.CharField(required=False, allow_blank=True)
    accountNumber = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        if "firstName" in validated_data:
            instance.first_name = validated_data["firstName"]
        if "lastName" in validated_data:
            instance.last_name = validated_data["lastName"]
        if "email" in validated_data:
            instance.email = validated_data["email"]
        instance.save(update_fields=["first_name", "last_name", "email"])

        profile, _ = UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                "sourceUserId": str(instance.id),
                "checkNumber": instance.username,
            },
        )
        if "middleName" in validated_data:
            profile.middleName = validated_data["middleName"]
        if "phone" in validated_data:
            profile.phone = validated_data["phone"]
        if "photo" in validated_data:
            profile.photo = validated_data["photo"]
        if "dutyStation" in validated_data:
            profile.dutyStation = validated_data["dutyStation"]
        if "bank" in validated_data:
            profile.bank = validated_data["bank"]
        if "accountNumber" in validated_data:
            profile.accountNumber = validated_data["accountNumber"]
        profile.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["currentPassword"]):
            raise serializers.ValidationError({"currentPassword": "Current password is incorrect."})
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["newPassword"])
        user.save(update_fields=["password"])

        profile = getattr(user, "profile", None)
        if profile and profile.mustChangePassword:
            profile.mustChangePassword = False
            profile.save(update_fields=["mustChangePassword"])


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    roles = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password", "roles"]

    def create(self, validated_data):
        roles = validated_data.pop("roles", [])
        user = User(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "sourceUserId": str(user.id),
                "checkNumber": user.username,
            },
        )
        if roles:
            groups = Group.objects.filter(name__in=roles)
            user.groups.set(groups)
        return user


class AuthTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        roles = list(user.groups.values_list("name", flat=True))
        perms = set(user.user_permissions.values_list("content_type__app_label", "codename"))
        for group in user.groups.all():
            perms.update(group.permissions.values_list("content_type__app_label", "codename"))
        token["roles"] = roles
        token["permissions"] = sorted(f"{app}.{code}" for app, code in perms)
        token["username"] = user.username
        profile = getattr(user, "profile", None)
        token["check_number"] = profile.checkNumber if profile else user.username
        token["source_user_id"] = profile.sourceUserId if profile and profile.sourceUserId else str(user.id)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
