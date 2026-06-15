import re
from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    """
    Enforces: min 8 chars, at least one uppercase letter,
    one lowercase letter, one digit, one special character.
    """

    def validate(self, password, user=None):
        errors = []
        if len(password) < 8:
            errors.append("at least 8 characters")
        if not re.search(r'[A-Z]', password):
            errors.append("at least one uppercase letter (A-Z)")
        if not re.search(r'[a-z]', password):
            errors.append("at least one lowercase letter (a-z)")
        if not re.search(r'\d', password):
            errors.append("at least one number (0-9)")
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>/?\\|`~]', password):
            errors.append("at least one special character (!@#$%...)")
        if errors:
            raise ValidationError(
                f"Password must contain: {', '.join(errors)}.",
                code='password_too_weak',
            )

    def get_help_text(self):
        return ''
