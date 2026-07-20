from django.db import transaction
from django.utils import timezone
from celery import shared_task

from apps.identity.models import EmployeeImportBatch, EmployeeImportRow
from apps.identity.serializers import AdminUserWriteSerializer
from apps.identity.services.access_delivery import deliver_temporary_password


@shared_task(name="identity.process_employee_import_row")
def process_employee_import_row_task(row_id: int) -> dict:
    try:
        row = EmployeeImportRow.objects.select_related("batch").get(id=row_id)
    except EmployeeImportRow.DoesNotExist:
        return {"rowId": row_id, "status": "failed", "error": "Row no longer exists."}

    if row.status != "pending":
        return {"rowId": row_id, "status": row.status}

    payload = {
        "checkNumber": row.checkNumber,
        "firstName": row.firstName,
        "lastName": row.lastName,
        "email": row.email,
    }
    for extra in ("personnelNumber", "departmentId", "designationId", "designation"):
        value = getattr(row, extra)
        if value:
            payload[extra] = value

    try:
        serializer = AdminUserWriteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
    except Exception as exc:  # noqa: BLE001 - any failure here is a per-row result, not a worker crash
        row.status = "failed"
        row.errorMessage = str(exc)[:2000]
        row.save(update_fields=["status", "errorMessage"])
        _maybe_complete_batch(row.batch_id)
        return {"rowId": row_id, "status": "failed", "error": row.errorMessage}

    email_sent = False
    generated_password = getattr(user, "_generated_password", None)
    if generated_password:
        email_sent, _message, _ = deliver_temporary_password(
            user,
            reason="created",
            password=generated_password,
            missing_email_message="Employee email is required before sending account access.",
            archived_message="Archived employees must be reactivated before sending account access.",
        )

    row.status = "created"
    row.emailSent = email_sent
    row.createdUserId = str(getattr(user.profile, "sourceUserId", "") or user.id)
    row.save(update_fields=["status", "emailSent", "createdUserId"])
    _maybe_complete_batch(row.batch_id)
    return {"rowId": row_id, "status": "created", "emailSent": email_sent}


def _maybe_complete_batch(batch_id) -> None:
    with transaction.atomic():
        batch = EmployeeImportBatch.objects.select_for_update().get(id=batch_id)
        if batch.status == "completed":
            return
        still_pending = batch.rows.filter(status="pending").exists()
        if not still_pending:
            batch.status = "completed"
            batch.completedAt = timezone.now()
            batch.save(update_fields=["status", "completedAt"])
