from django.core.validators import RegexValidator

# GST check numbers are exactly nine digits. They double as the login username.
validate_check_number = RegexValidator(
    regex=r"^\d{9}$",
    message="Check number must be exactly 9 digits.",
    code="invalid_check_number",
)
