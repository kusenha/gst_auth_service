import uuid

from django.conf import settings
from django.db import models


class ServiceClient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    clientId = models.CharField(max_length=120, unique=True)
    clientSecret = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    createdAt = models.DateTimeField(auto_now_add=True)


class RefreshTokenAudit(models.Model):
    userId = models.IntegerField(db_index=True)
    jti = models.CharField(max_length=255, unique=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    revokedAt = models.DateTimeField(null=True, blank=True)


class UserProfile(models.Model):
    GENDER_CHOICES = (("Male", "Male"), ("Female", "Female"))
    STATUS_CHOICES = (("Active", "Active"), ("On Leave", "On Leave"), ("Retired", "Retired"), ("Archived", "Archived"))

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    sourceUserId = models.CharField(max_length=50, unique=True, db_index=True)
    checkNumber = models.CharField(max_length=50, unique=True)
    personnelNumber = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)
    middleName = models.CharField(max_length=120, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="Male")
    phone = models.CharField(max_length=30, blank=True)
    departmentId = models.CharField(max_length=50, blank=True)
    # Loose reference to apps.organization.OrganisationalUnit.id — not a real
    # FK, matching that model's own documented stance that it deliberately
    # doesn't share an identifier space with this app. This is what lets a
    # claim form auto-fill "the requester's own directorate/unit" instead of
    # asking them to pick one and risk choosing the wrong one.
    organisationalUnitId = models.IntegerField(null=True, blank=True)
    designationId = models.IntegerField(null=True, blank=True)
    designationName = models.CharField(max_length=120, blank=True)
    education = models.CharField(max_length=60, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    salaryScale = models.CharField(max_length=30, blank=True)
    dutyStation = models.CharField(max_length=120, blank=True)
    region = models.CharField(max_length=120, blank=True)
    dateEmployed = models.DateField(null=True, blank=True)
    bank = models.CharField(max_length=120, blank=True)
    accountNumber = models.CharField(max_length=50, blank=True)
    taxNumber = models.CharField(max_length=50, blank=True)
    nida = models.CharField(max_length=50, blank=True)
    supervisorId = models.CharField(max_length=50, blank=True)
    photo = models.URLField(blank=True)
    role = models.CharField(max_length=80, default="employee")
    mustChangePassword = models.BooleanField(default=False)
    accountEmailStatus = models.CharField(max_length=30, default="not_sent")
    accountEmailSentAt = models.DateTimeField(null=True, blank=True)
    accountEmailError = models.TextField(blank=True)
    # Any access/refresh token issued before this timestamp is rejected on
    # its next use, regardless of its own expiry — set on logout so that a
    # token already held by another GST EDA app/tab becomes invalid
    # immediately instead of only converging eventually via polling.
    tokensInvalidBefore = models.DateTimeField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)


class EmployeeImportBatch(models.Model):
    """One bulk-upload of employees (see apps.identity.views.EmployeeImportView).
    Rows are created and emailed asynchronously by apps.identity.tasks — this
    row tracks overall progress for the uploading admin to poll."""

    STATUS_CHOICES = (("processing", "Processing"), ("completed", "Completed"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fileName = models.CharField(max_length=255, blank=True)
    createdBy = models.CharField(max_length=120, blank=True)
    totalRows = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="processing")
    createdAt = models.DateTimeField(auto_now_add=True)
    completedAt = models.DateTimeField(null=True, blank=True)


class EmployeeImportRow(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("created", "Created"),
        ("failed", "Failed"),
    )

    batch = models.ForeignKey(EmployeeImportBatch, related_name="rows", on_delete=models.CASCADE)
    rowNumber = models.PositiveIntegerField()
    checkNumber = models.CharField(max_length=50, blank=True)
    personnelNumber = models.CharField(max_length=50, blank=True)
    firstName = models.CharField(max_length=150, blank=True)
    lastName = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    departmentId = models.CharField(max_length=50, blank=True)
    designationId = models.IntegerField(null=True, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    errorMessage = models.TextField(blank=True)
    emailSent = models.BooleanField(default=False)
    createdUserId = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["rowNumber"]
