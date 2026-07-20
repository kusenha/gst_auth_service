import secrets
import re

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.identity.models import UserProfile
from apps.identity.services.designations import resolve_designation_name
from apps.identity.services.profiles import ProfileConflictError, ensure_user_profile

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
    services = serializers.SerializerMethodField()
    tokensInvalidBefore = serializers.SerializerMethodField()

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
            "services",
            "tokensInvalidBefore",
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
        designation_name = resolve_designation_name(profile.designationId, profile.designationName)
        if designation_name and designation_name != profile.designationName:
            profile.designationName = designation_name
            profile.save(update_fields=["designationName"])
        return designation_name or (str(profile.designationId) if profile.designationId else "")

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

    def get_tokensInvalidBefore(self, obj):
        # Lets other services (eda_backend, configuration_service) that
        # decode this app's JWTs locally reject a token whose `iat` predates
        # the user's last logout, instead of only relying on natural JWT
        # expiry — see apps.identity.authentication.CutoffAwareJWTAuthentication.
        profile = self._profile(obj)
        return profile.tokensInvalidBefore.isoformat() if profile and profile.tokensInvalidBefore else None

    def get_accountEmailError(self, obj):
        profile = self._profile(obj)
        return profile.accountEmailError if profile else ""

    def get_permissionKeys(self, obj):
        from apps.rbac.services import resolve_permission_keys

        return resolve_permission_keys(obj)

    def get_services(self, obj):
        from apps.rbac.services import resolve_service_keys

        return resolve_service_keys(obj)


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

        try:
            profile = ensure_user_profile(instance, source_user_id=str(instance.id), check_number=instance.username)
        except ProfileConflictError as exc:
            raise serializers.ValidationError({"id": str(exc)}) from exc
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


class TemporaryPasswordChangeSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    currentPassword = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        username = str(attrs.get("username", "")).strip()
        user = (
            User.objects.filter(username__iexact=username).select_related("profile").first()
            or User.objects.filter(email__iexact=username).select_related("profile").first()
            or User.objects.filter(profile__checkNumber__iexact=username).select_related("profile").first()
        )
        if not user:
            raise serializers.ValidationError({"username": "User not found."})

        profile = getattr(user, "profile", None)
        if not user.is_active or (profile and profile.status == "Archived"):
            raise serializers.ValidationError(
                {"detail": "This employee account has been archived or deactivated. Contact HR to reactivate it."}
            )
        if not profile or not profile.mustChangePassword:
            raise serializers.ValidationError(
                {"detail": "This account does not require a temporary password change."}
            )
        if not user.check_password(attrs["currentPassword"]):
            raise serializers.ValidationError({"currentPassword": "Temporary password is incorrect."})

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["newPassword"])
        user.save(update_fields=["password"])

        profile = getattr(user, "profile", None)
        if profile and profile.mustChangePassword:
            profile.mustChangePassword = False
            profile.save(update_fields=["mustChangePassword"])
        return user


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
        try:
            ensure_user_profile(user, source_user_id=str(user.id), check_number=user.username)
        except ProfileConflictError as exc:
            raise serializers.ValidationError({"id": str(exc)}) from exc
        if roles:
            groups = Group.objects.filter(name__in=roles)
            user.groups.set(groups)
        return user


class AuthTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        from apps.rbac.services import resolve_permission_keys, resolve_service_keys

        token = super().get_token(user)
        roles = list(user.groups.values_list("name", flat=True))
        token["roles"] = roles
        token["permissions"] = resolve_permission_keys(user)
        token["services"] = resolve_service_keys(user)
        token["username"] = user.username
        profile = getattr(user, "profile", None)
        token["check_number"] = profile.checkNumber if profile else user.username
        token["source_user_id"] = profile.sourceUserId if profile and profile.sourceUserId else str(user.id)
        token["role"] = profile.role if profile and profile.role else (roles[0] if roles else "employee")
        token["department_id"] = profile.departmentId if profile else ""
        token["designation_id"] = profile.designationId if profile else None
        token["designation_name"] = (
            resolve_designation_name(profile.designationId, profile.designationName)
            if profile
            else ""
        )
        token["status"] = profile.status if profile else "Active"
        token["email"] = user.email
        token["full_name"] = f"{user.first_name} {user.last_name}".strip()
        return token

    def validate(self, attrs):
        username = str(attrs.get(self.username_field, "")).strip()
        if username:
            user = (
                User.objects.filter(username__iexact=username).select_related("profile").first()
                or User.objects.filter(email__iexact=username).select_related("profile").first()
                or User.objects.filter(profile__checkNumber__iexact=username).select_related("profile").first()
            )
            if user and (not user.is_active or (getattr(user, "profile", None) and user.profile.status == "Archived")):
                raise serializers.ValidationError(
                    {"detail": "This employee account has been archived or deactivated. Contact HR to reactivate it."}
                )
            if user:
                attrs[self.username_field] = user.get_username()

        password = attrs.get("password", "")
        authenticated_user = authenticate(
            request=self.context.get("request"),
            **{self.username_field: attrs.get(self.username_field, ""), "password": password},
        )
        if authenticated_user:
            profile = getattr(authenticated_user, "profile", None)
            if profile and profile.mustChangePassword:
                self.user = authenticated_user
                return {
                    "user": UserSerializer(authenticated_user).data,
                    "requiresPasswordChange": True,
                }

        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class AdminUserWriteSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=False)
    checkNumber = serializers.CharField(required=True)
    personnelNumber = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    firstName = serializers.CharField(required=False, allow_blank=True)
    middleName = serializers.CharField(required=False, allow_blank=True)
    lastName = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=["Male", "Female"], required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    departmentId = serializers.CharField(required=False, allow_blank=True)
    designationId = serializers.IntegerField(required=False, allow_null=True)
    designation = serializers.CharField(required=False, allow_blank=True)
    education = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["Active", "On Leave", "Retired", "Archived"], required=False)
    salaryScale = serializers.CharField(required=False, allow_blank=True)
    dutyStation = serializers.CharField(required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    dateEmployed = serializers.DateField(required=False, allow_null=True)
    bank = serializers.CharField(required=False, allow_blank=True)
    accountNumber = serializers.CharField(required=False, allow_blank=True)
    taxNumber = serializers.CharField(required=False, allow_blank=True)
    nida = serializers.CharField(required=False, allow_blank=True)
    supervisorId = serializers.CharField(required=False, allow_blank=True)
    photo = serializers.URLField(required=False, allow_blank=True)
    role = serializers.CharField(required=False, allow_blank=True)
    mustChangePassword = serializers.BooleanField(required=False)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def _defaults(self) -> dict:
        return {
            "sourceUserId": "",
            "checkNumber": "",
            "personnelNumber": None,
            "middleName": "",
            "gender": "Male",
            "phone": "",
            "departmentId": "",
            "designationId": None,
            "designationName": "",
            "education": "",
            "status": "Active",
            "salaryScale": "",
            "dutyStation": "",
            "region": "",
            "dateEmployed": None,
            "bank": "",
            "accountNumber": "",
            "taxNumber": "",
            "nida": "",
            "supervisorId": "",
            "photo": "",
            "role": "employee",
            "mustChangePassword": False,
            "accountEmailStatus": "not_sent",
            "accountEmailSentAt": None,
            "accountEmailError": "",
        }

    def _sync_role_group(self, user, role: str):
        if not role:
            return
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.set([group])

    def _resolve_profile_for_create(self, source_user_id: str, check_number: str):
        if source_user_id:
            profile = UserProfile.objects.select_related("user").filter(sourceUserId=source_user_id).first()
            if profile:
                return profile

        profile = UserProfile.objects.select_related("user").filter(checkNumber=check_number).first()
        if profile:
            return profile

        return None

    @staticmethod
    def _normalize_source_user_id(source_user_id: str) -> str:
        value = str(source_user_id or "").strip()
        # Ignore frontend-only temporary ids like e-1723456789012 and let
        # auth_service assign the canonical identifier.
        if re.fullmatch(r"e-\d{10,}", value):
            return ""
        return value

    def _get_or_init_profile(self, user, source_user_id: str, check_number: str):
        profile = getattr(user, "profile", None)
        if profile:
            return profile, False

        existing = None
        if source_user_id:
            existing = UserProfile.objects.select_related("user").filter(sourceUserId=source_user_id).first()
        if existing and existing.user_id != user.id:
            raise serializers.ValidationError(
                {"id": f"Employee source id '{source_user_id}' is already linked to another account."}
            )
        if not existing and check_number:
            existing = UserProfile.objects.select_related("user").filter(checkNumber=check_number).first()
        if existing and existing.user_id != user.id:
            raise serializers.ValidationError(
                {"checkNumber": f"Check number '{check_number}' is already linked to another account."}
            )
        if existing:
            return existing, False

        profile = UserProfile(
            user=user,
            sourceUserId=source_user_id or str(user.id),
            checkNumber=check_number,
        )
        return profile, True

    def create(self, validated_data):
        password = validated_data.pop("password", "") or secrets.token_urlsafe(10)
        source_user_id = self._normalize_source_user_id(validated_data.pop("id", ""))
        check_number = validated_data["checkNumber"]
        status_value = validated_data.get("status", "Active")
        must_change_password = (
            bool(validated_data["mustChangePassword"])
            if "mustChangePassword" in validated_data
            else True
        )

        existing_profile = self._resolve_profile_for_create(source_user_id, check_number)
        if existing_profile:
            update_data = dict(validated_data)
            if source_user_id:
                update_data["id"] = source_user_id
            update_data["password"] = password
            update_data.setdefault("mustChangePassword", must_change_password)
            return self.update(existing_profile.user, update_data)

        user = User(
            username=check_number,
            email=validated_data.get("email", ""),
            first_name=validated_data.get("firstName", ""),
            last_name=validated_data.get("lastName", ""),
            is_active=status_value != "Archived",
        )
        user.set_password(password)
        user.save()
        user._generated_password = password  # type: ignore[attr-defined]

        profile, _ = self._get_or_init_profile(user, source_user_id, check_number)
        profile.sourceUserId = source_user_id or str(user.id)
        profile.checkNumber = check_number
        profile.personnelNumber = validated_data.get("personnelNumber") or None
        profile.middleName = validated_data.get("middleName", "")
        profile.gender = validated_data.get("gender", "Male")
        profile.phone = validated_data.get("phone", "")
        profile.departmentId = validated_data.get("departmentId", "")
        designation_id = validated_data.get("designationId")
        profile.designationId = designation_id
        profile.designationName = resolve_designation_name(
            designation_id,
            validated_data.get("designation", ""),
        )
        profile.education = validated_data.get("education", "")
        profile.status = status_value
        profile.salaryScale = validated_data.get("salaryScale", "")
        profile.dutyStation = validated_data.get("dutyStation", "")
        profile.region = validated_data.get("region", "")
        profile.dateEmployed = validated_data.get("dateEmployed")
        profile.bank = validated_data.get("bank", "")
        profile.accountNumber = validated_data.get("accountNumber", "")
        profile.taxNumber = validated_data.get("taxNumber", "")
        profile.nida = validated_data.get("nida", "")
        profile.supervisorId = validated_data.get("supervisorId", "")
        profile.photo = validated_data.get("photo", "")
        profile.role = validated_data.get("role", "employee") or "employee"
        profile.mustChangePassword = must_change_password
        profile.accountEmailStatus = "pending" if user.email else "failed"
        profile.accountEmailError = "" if user.email else "User email is required for account delivery."
        profile.save()
        self._sync_role_group(user, profile.role)
        return user

    def update(self, instance, validated_data):
        check_number = validated_data.get("checkNumber", instance.username)
        instance.username = check_number
        if "email" in validated_data:
            instance.email = validated_data.get("email", "")
        if "firstName" in validated_data:
            instance.first_name = validated_data.get("firstName", "")
        if "lastName" in validated_data:
            instance.last_name = validated_data.get("lastName", "")
        if "status" in validated_data:
            instance.is_active = validated_data.get("status") != "Archived"

        password = validated_data.get("password", "")
        if password:
            instance.set_password(password)
            instance._generated_password = password  # type: ignore[attr-defined]

        update_fields = ["username", "email", "first_name", "last_name"]
        if "status" in validated_data:
            update_fields.append("is_active")
        if password:
            update_fields.append("password")
        instance.save(update_fields=update_fields)

        source_user_id = self._normalize_source_user_id(
            validated_data.get("id", getattr(getattr(instance, "profile", None), "sourceUserId", "") or str(instance.id))
        )
        profile, _ = self._get_or_init_profile(instance, source_user_id, check_number)
        conflicting_profile = (
            UserProfile.objects.exclude(user=instance)
            .filter(sourceUserId=source_user_id)
            .first()
            if source_user_id
            else None
        )
        if conflicting_profile:
            raise serializers.ValidationError(
                {"id": f"Employee source id '{source_user_id}' is already linked to another account."}
            )
        conflicting_check_number = (
            UserProfile.objects.exclude(user=instance)
            .filter(checkNumber=check_number)
            .first()
            if check_number
            else None
        )
        if conflicting_check_number:
            raise serializers.ValidationError(
                {"checkNumber": f"Check number '{check_number}' is already linked to another account."}
            )

        profile.sourceUserId = source_user_id
        profile.checkNumber = check_number
        if "personnelNumber" in validated_data:
            profile.personnelNumber = validated_data.get("personnelNumber") or None
        if "middleName" in validated_data:
            profile.middleName = validated_data.get("middleName", "")
        if "gender" in validated_data:
            profile.gender = validated_data.get("gender", "Male")
        if "phone" in validated_data:
            profile.phone = validated_data.get("phone", "")
        if "departmentId" in validated_data:
            profile.departmentId = validated_data.get("departmentId", "")
        if "designationId" in validated_data:
            profile.designationId = validated_data.get("designationId")
        if "designation" in validated_data:
            profile.designationName = validated_data.get("designation", "")
        if "designationId" in validated_data or "designation" in validated_data:
            profile.designationName = resolve_designation_name(
                profile.designationId,
                profile.designationName,
            )
        if "education" in validated_data:
            profile.education = validated_data.get("education", "")
        if "status" in validated_data:
            profile.status = validated_data.get("status", "Active")
        if "salaryScale" in validated_data:
            profile.salaryScale = validated_data.get("salaryScale", "")
        if "dutyStation" in validated_data:
            profile.dutyStation = validated_data.get("dutyStation", "")
        if "region" in validated_data:
            profile.region = validated_data.get("region", "")
        if "dateEmployed" in validated_data:
            profile.dateEmployed = validated_data.get("dateEmployed")
        if "bank" in validated_data:
            profile.bank = validated_data.get("bank", "")
        if "accountNumber" in validated_data:
            profile.accountNumber = validated_data.get("accountNumber", "")
        if "taxNumber" in validated_data:
            profile.taxNumber = validated_data.get("taxNumber", "")
        if "nida" in validated_data:
            profile.nida = validated_data.get("nida", "")
        if "supervisorId" in validated_data:
            profile.supervisorId = validated_data.get("supervisorId", "")
        if "photo" in validated_data:
            profile.photo = validated_data.get("photo", "")
        if "mustChangePassword" in validated_data:
            profile.mustChangePassword = bool(validated_data.get("mustChangePassword", False))
        if "role" in validated_data:
            profile.role = validated_data.get("role", "employee") or "employee"

        profile.save()
        self._sync_role_group(instance, profile.role)
        return instance


class AdminResetPasswordSerializer(serializers.Serializer):
    newPassword = serializers.CharField(write_only=True, min_length=8, required=False, allow_blank=True)


class SetUserStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["Active", "On Leave", "Retired", "Archived"])


class AssignRoleSerializer(serializers.Serializer):
    role = serializers.CharField(required=True)


class AssignPermissionsSerializer(serializers.Serializer):
    permissions = serializers.ListField(child=serializers.CharField(), required=True)

    def validate_permissions(self, value):
        from apps.rbac.models import Permission as RbacPermission

        cleaned = {str(item).strip() for item in value if str(item).strip()}
        matched = list(RbacPermission.objects.filter(key__in=cleaned).values_list("id", "key"))
        matched_keys = {key for _, key in matched}
        invalid = sorted(cleaned - matched_keys)

        if invalid:
            raise serializers.ValidationError(f"Unknown permissions: {', '.join(invalid)}")

        return sorted({pid for pid, _ in matched})
