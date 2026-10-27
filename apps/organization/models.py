from django.db import models


class Department(models.Model):
    """Platform-wide department master. Every service reads departments from
    here — eda-service keeps a read-only replica only for its own foreign
    keys (task catalog, designation rates). IDs are the same strings the
    rest of the platform already stores as departmentId (e.g. "d1")."""

    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=120, unique=True)
    # Employee sourceUserId of the department head, same convention as
    # OrganisationalUnitHead.employeeId.
    headId = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Designation(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="designations",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=120)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("department", "name")

    def __str__(self) -> str:
        if self.department_id:
            return f"{self.department.name} - {self.name}"
        return self.name


class OrganisationalUnit(models.Model):
    """Directorate/Department/Unit/Section hierarchy, shared across every GST
    service that needs to resolve "who approves for this part of the
    org chart" — owned here so no downstream service maintains its own copy
    of heads of directorate/department/unit/section.

    Separate from Department above: Department is the flat HR structure
    employees belong to, this is the leadership/approval hierarchy used by
    claim-request-service. The two don't share an identifier space yet.
    """

    UNIT_TYPE_CHOICES = [
        ("DIRECTORATE", "Directorate"),
        ("DEPARTMENT", "Department"),
        ("UNIT", "Unit"),
        ("SECTION", "Section"),
    ]

    name = models.CharField(max_length=150)
    unitType = models.CharField(max_length=20, choices=UNIT_TYPE_CHOICES)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    isActive = models.BooleanField(default=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class OrganisationalUnitHead(models.Model):
    """Who currently heads a given organisational unit. Effective-dated so a
    change in leadership doesn't lose history, and so a request whose
    approval step already resolved-and-stored a specific approver (see
    claim-request-service's workflow engine) isn't retroactively affected by
    a later change here."""

    LEADERSHIP_ROLE_CHOICES = [
        ("HEAD_OF_DIRECTORATE", "Head of Directorate"),
        ("HEAD_OF_DEPARTMENT", "Head of Department"),
        ("HEAD_OF_UNIT", "Head of Unit"),
        ("HEAD_OF_SECTION", "Head of Section"),
    ]

    organisationalUnit = models.ForeignKey(
        OrganisationalUnit, on_delete=models.CASCADE, related_name="heads"
    )
    # Plain string, not a FK to auth_service's own User table — this should
    # read as "an identity", the same convention every downstream service
    # uses for employeeId, kept consistent here even though it's same-DB.
    employeeId = models.CharField(max_length=50, db_index=True)
    leadershipRole = models.CharField(max_length=30, choices=LEADERSHIP_ROLE_CHOICES)
    isActing = models.BooleanField(default=False)
    effectiveFrom = models.DateField()
    effectiveTo = models.DateField(null=True, blank=True)
    isActive = models.BooleanField(default=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-effectiveFrom"]

    def __str__(self) -> str:
        return f"{self.organisationalUnit_id}:{self.leadershipRole}:{self.employeeId}"
