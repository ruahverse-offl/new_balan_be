"""
Shared password strength rules for registration, password change, and staff user create/update.
"""

import re

PASSWORD_POLICY_MESSAGE = (
    "Password must be at least 8 characters and include at least one uppercase letter, "
    "one lowercase letter, and one special character."
)

_UPPER = re.compile(r"[A-Z]")
_LOWER = re.compile(r"[a-z]")
_SPECIAL = re.compile(r"[^A-Za-z0-9]")


def assert_password_meets_policy(password: str) -> None:
    """
    Enforce password policy. Raises ValueError with a stable user-facing message if invalid.

    Args:
        password: Plain-text password to check.

    Raises:
        ValueError: When the password does not meet policy.
    """
    if not isinstance(password, str):
        raise ValueError(PASSWORD_POLICY_MESSAGE)
    pwd = password.strip()
    if len(pwd) < 8 or not _UPPER.search(pwd) or not _LOWER.search(pwd) or not _SPECIAL.search(pwd):
        raise ValueError(PASSWORD_POLICY_MESSAGE)
