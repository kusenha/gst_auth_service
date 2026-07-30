from django.db import models


class OrganisationalUnit(models.Model):
    """Directorate/Department/Unit/Section hierarchy, shared across every GST
    service that needs to resolve "who approves for this part of the
    org chart" — owned here so no downstream service maintains its own copy
    of heads of directorate/department/unit/section.

    Deliberately separate from eda_backend's own (flat, single-level)
    Department model — that one is EDA's org-chart-for-its-own-purposes,
    this one is the platform-wide leadership/approval hierarchy. The two
    are not guaranteed to share an identifier space; reconciling them is
    out of scope here.
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
