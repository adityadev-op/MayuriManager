import os
import secrets
from dataclasses import dataclass


class CredentialConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class AuthenticatedAccount:
    username: str
    display_name: str
    account_type: str
    employee_id: int | None = None
    job_role: str | None = None


_EMPLOYEE_ACCOUNTS = (
    ("RECEPTIONIST", "Aaray Sharma", "Receptionist"),
    ("CASHIER", "Diya Patel", "Cashier"),
    ("MANAGER", "Tara Nair", "Manager"),
)
_ADMIN_ACCOUNTS = (
    ("ADITYA", "Aditya"),
    ("PUSHPRAJ", "Pushpraj"),
    ("DEEPAK", "Deepak"),
)


def _required_setting(name):
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise CredentialConfigurationError(
            f"Required login setting {name} is missing from the local dotenv files."
        )
    return value


def _matches(value, expected):
    return secrets.compare_digest(
        value.casefold().encode("utf-8"),
        expected.casefold().encode("utf-8"),
    )


def authenticate_employee(username, password):
    for account_key, display_name, job_role in _EMPLOYEE_ACCOUNTS:
        prefix = f"MAYURICAFE_EMPLOYEE_{account_key}"
        configured_username = _required_setting(f"{prefix}_USERNAME").strip()
        configured_password = _required_setting(f"{prefix}_PASSWORD")
        employee_id_value = _required_setting(f"{prefix}_ID").strip()
        try:
            employee_id = int(employee_id_value)
        except ValueError as error:
            raise CredentialConfigurationError(
                f"{prefix}_ID must be a positive employee ID."
            ) from error
        if employee_id < 1:
            raise CredentialConfigurationError(
                f"{prefix}_ID must be a positive employee ID."
            )

        if _matches(username, configured_username) and secrets.compare_digest(
            password.encode("utf-8"),
            configured_password.encode("utf-8"),
        ):
            return AuthenticatedAccount(
                username=configured_username,
                display_name=display_name,
                account_type="employee",
                employee_id=employee_id,
                job_role=job_role,
            )
    return None


def authenticate_admin(username, password):
    for account_key, display_name in _ADMIN_ACCOUNTS:
        prefix = f"MAYURICAFE_ADMIN_{account_key}"
        configured_username = _required_setting(f"{prefix}_USERNAME").strip()
        configured_password = _required_setting(f"{prefix}_PASSWORD")

        if _matches(username, configured_username) and secrets.compare_digest(
            password.encode("utf-8"),
            configured_password.encode("utf-8"),
        ):
            return AuthenticatedAccount(
                username=configured_username,
                display_name=display_name,
                account_type="admin",
            )
    return None
