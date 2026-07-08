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
    STATUS_CHOICES = (("Active", "Active"), ("On Leave", "On Leave"), ("Retired", "Retired"))

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    sourceUserId = models.CharField(max_length=50, unique=True, db_index=True)
    checkNumber = models.CharField(max_length=50, unique=True)
    personnelNumber = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)
    middleName = models.CharField(max_length=120, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="Male")
    phone = models.CharField(max_length=30, blank=True)
    departmentId = models.CharField(max_length=50, blank=True)
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
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
