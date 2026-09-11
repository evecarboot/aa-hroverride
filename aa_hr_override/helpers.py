"""Centralised permission helpers.

All override-permission logic lives here so it can be reused by views,
templates (via context), the admin, and tests without duplication.
"""

from django.contrib.auth.models import User

#: The codename of the custom permission declared on
#: ``HRApplicationOverrideLog.Meta.permissions``.
OVERRIDE_PERMISSION = "aa_hr_override.override_application"


def can_override_hr_application(user: User) -> bool:
    """Return ``True`` if *user* may bypass the reviewer-ownership check.

    Superusers always pass.  Non-superusers must hold the
    ``aa_hr_override.override_application`` permission.
    """
    if not user or not user.is_authenticated:
        return False
    return bool(user.is_superuser or user.has_perm(OVERRIDE_PERMISSION))


def can_takeover_application(user: User) -> bool:
    """Return ``True`` if *user* may take over (re-assign) an application.

    Requires ``auth.human_resources`` **and** the override permission
    (or superuser status).
    """
    if not user or not user.is_authenticated:
        return False
    if not user.has_perm("auth.human_resources"):
        return False
    return can_override_hr_application(user)


def can_approve_override(user: User) -> bool:
    """Return ``True`` if *user* may approve an application they don't own.

    Requires ``auth.human_resources``, ``hrapplications.approve_application``
    **and** the override permission (or superuser status).
    """
    if not user or not user.is_authenticated:
        return False
    if not user.has_perm("auth.human_resources"):
        return False
    if not user.has_perm("hrapplications.approve_application"):
        return False
    return can_override_hr_application(user)


def can_reject_override(user: User) -> bool:
    """Return ``True`` if *user* may reject an application they don't own.

    Requires ``auth.human_resources``, ``hrapplications.reject_application``
    **and** the override permission (or superuser status).
    """
    if not user or not user.is_authenticated:
        return False
    if not user.has_perm("auth.human_resources"):
        return False
    if not user.has_perm("hrapplications.reject_application"):
        return False
    return can_override_hr_application(user)
