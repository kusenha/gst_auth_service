import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def send_temporary_password_email(user: User, temporary_password: str, *, reason: str) -> tuple[str, str]:
    """Returns (status, message) where status is one of:
    "sent" - delivered directly through the Notification Service.
    "queued" - the Notification Service is unreachable; the Core Gateway
        accepted the event and will deliver it once that service recovers.
    "failed" - could not be delivered and could not be queued either.
    """
    if not user.email:
        return "failed", "User email is required to deliver a temporary password."

    base_url = settings.NOTIFICATION_SERVICE_URL.strip()
    if not base_url:
        return "failed", "Notification service URL is not configured."

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
    ok, detail = _send_direct(base_url, payload)
    if ok:
        return "sent", ""

    if detail == "unreachable":
        relayed, relay_detail = _relay_via_core_gateway(payload)
        if relayed:
            return "queued", (
                "The notification service is temporarily unavailable. The message has been "
                "handed to the Core Gateway and will be delivered automatically once the "
                "notification service is back online."
            )
        return "failed", "Notification service is unreachable and the Core Gateway could not queue it either."

    return "failed", detail


def _send_direct(base_url: str, payload: dict) -> tuple[bool, str]:
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
            body = {}
            if payload_text:
                try:
                    body = json.loads(payload_text)
                except json.JSONDecodeError:
                    body = {}

            if 200 <= response.status < 300:
                delivery_status = str(body.get("status", "")).strip().lower()
                if delivery_status in {"failed", "partial", "skipped"}:
                    return False, str(body.get("providerResponse") or "Notification service did not deliver the email.")
                return True, ""
            return False, f"Notification service returned HTTP {response.status}."
    except HTTPError as exc:
        body = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
        return False, body or f"Notification service returned HTTP {exc.code}."
    except URLError:
        return False, "unreachable"


def _relay_via_core_gateway(payload: dict) -> tuple[bool, str]:
    """Fallback used when the Notification Service cannot be reached
    directly: hand the event to the Core Gateway, which will hold it and
    deliver it automatically once the Notification Service is healthy again."""
    base = getattr(settings, "DISCOVERY_SERVICE_URL", "").rstrip("/")
    if not base:
        return False, "Core Gateway URL is not configured."

    headers = {"Content-Type": "application/json"}
    if settings.DISCOVERY_SHARED_TOKEN:
        headers["X-Service-Token"] = settings.DISCOVERY_SHARED_TOKEN

    body = json.dumps({"targetService": "notification-service", "payload": payload}).encode("utf-8")
    request = Request(url=f"{base}/notifications/relay/", data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=5.0) as response:
            if 200 <= response.status < 300:
                return True, "Accepted by Core Gateway for queued delivery."
            return False, f"Core Gateway returned HTTP {response.status}."
    except (HTTPError, URLError, TimeoutError):
        return False, "Core Gateway is also unreachable."


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
