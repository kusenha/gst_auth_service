import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def send_temporary_password_email(user: User, temporary_password: str, *, reason: str) -> tuple[bool, str]:
    if not user.email:
        return False, "User email is required to deliver a temporary password."

    base_url = settings.NOTIFICATION_SERVICE_URL.strip()
    if not base_url:
        return False, "Notification service URL is not configured."

    message = _build_message(user, temporary_password, reason=reason)
    subject = (
        "Your GST EDA account has been created"
        if reason == "created"
        else "Your GST EDA password has been reset"
    )
    payload = {
        "type": f"account.{reason}",
        "service": "auth-service",
        "user_id": _source_user_id(user),
        "email": user.email,
        "subject": subject,
        "title": subject,
        "body": message,
        "channels": ["email"],
    }

    # Account creation and password reset emails are critical user flows.
    # Process them synchronously through notification_service so the caller
    # gets a real delivery result instead of a queued-only acknowledgement.
    query = urlencode({"queue": "false"})
    headers = {"Content-Type": "application/json"}
    if settings.NOTIFICATION_INTERNAL_TOKEN:
        headers["X-Internal-Token"] = settings.NOTIFICATION_INTERNAL_TOKEN
    request = Request(
        url=f"{base_url}?{query}",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.NOTIFICATION_SERVICE_TIMEOUT_SECONDS) as response:
            payload_text = response.read().decode("utf-8") if hasattr(response, "read") else ""
            payload = {}
            if payload_text:
                try:
                    payload = json.loads(payload_text)
                except json.JSONDecodeError:
                    payload = {}

            if 200 <= response.status < 300:
                delivery_status = str(payload.get("status", "")).strip().lower()
                if delivery_status in {"failed", "partial", "skipped"}:
                    return False, str(payload.get("providerResponse") or "Notification service did not deliver the email.")
                return True, ""
            return False, f"Notification service returned HTTP {response.status}."
    except HTTPError as exc:
        body = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
        return False, body or f"Notification service returned HTTP {exc.code}."
    except URLError:
        return False, "Notification service is unreachable."


def _source_user_id(user: User) -> str:
    profile = getattr(user, "profile", None)
    if profile and profile.sourceUserId:
        return profile.sourceUserId
    return str(user.id)


def _build_message(user: User, temporary_password: str, *, reason: str) -> str:
    greeting = user.first_name or getattr(user, "username", "") or "User"
    intro = "Your GST EDA account has been created." if reason == "created" else "Your GST EDA password has been reset."
    return (
        f"Hello {greeting},\n\n"
        f"{intro}\n"
        f"Check Number: {user.username}\n"
        f"Temporary Password: {temporary_password}\n\n"
        "Please sign in with this temporary password and change it immediately.\n"
    )
