"""Models for the HR Application Override plugin.

The single model ``HRApplicationOverrideLog`` serves two purposes:

1.  It stores a permanent audit trail of every override action taken by
    Directors / CEOs / senior HR staff.
2.  Its ``Meta.permissions`` declares the custom permission
    ``aa_hr_override.override_application`` that gates all override
    functionality.

The permission is intentionally declared on this model (rather than on a
dummy or proxy model) so that it is created automatically by Django's
migration system and shows up in the standard group/permission admin.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class HRApplicationOverrideLog(models.Model):
    """Audit-trail record for an override action on an HR application.

    Entries are **never** deleted when the underlying application or a
    referenced user is removed.  Foreign keys use ``SET_NULL`` so that the
    log row survives; the numeric ``application_pk_snapshot`` field
    preserves the original application ID even after deletion.
    """

    class Action(models.TextChoices):
        TAKEOVER = "TAKEOVER", _("Take Over")
        APPROVE_OVERRIDE = "APPROVE_OVERRIDE", _("Approve Override")
        REJECT_OVERRIDE = "REJECT_OVERRIDE", _("Reject Override")

    # Relationship to the application.  SET_NULL so the log survives
    # application deletion; the snapshot keeps the original PK.
    application = models.ForeignKey(
        "hrapplications.Application",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="override_logs",
        verbose_name=_("application"),
    )
    application_pk_snapshot = models.PositiveIntegerField(
        verbose_name=_("application ID"),
        help_text=_("Snapshot of the application PK at the time of the action."),
    )

    # Who performed the override.
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_override_actions",
        verbose_name=_("actor"),
    )

    # Reviewer state before / after (mainly relevant for takeovers).
    previous_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_override_previous_reviewer",
        verbose_name=_("previous reviewer"),
    )
    new_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_override_new_reviewer",
        verbose_name=_("new reviewer"),
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
        verbose_name=_("action"),
    )
    reason = models.TextField(
        blank=True,
        default="",
        verbose_name=_("reason"),
        help_text=_("Optional reason provided by the director for this override."),
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("timestamp"),
    )

    class Meta:
        verbose_name = _("HR Application Override Log")
        verbose_name_plural = _("HR Application Override Logs")
        ordering = ["-timestamp"]
        permissions = (
            (
                "override_application",
                "Can override HR application reviewer restrictions",
            ),
        )

    def __str__(self) -> str:
        return (
            f"OverrideLog(app#{self.application_pk_snapshot}, "
            f"{self.action}, {self.timestamp})"
        )
