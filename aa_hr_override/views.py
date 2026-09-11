"""Views for the HR Application Override plugin.

Every state-changing endpoint is **POST-only**.  GET requests receive a
405 Method Not Allowed.  All permission checks happen server-side – the
template merely hides buttons for usability, not for security.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from allianceauth.notifications import notify

from allianceauth.hrapplications.models import Application

from .forms import OverrideActionForm
from .helpers import (
    can_approve_override,
    can_reject_override,
    can_takeover_application,
)
from .models import HRApplicationOverrideLog

logger = logging.getLogger(__name__)

#: GET is never allowed for state-changing endpoints.
_POST_ONLY_METHODS = ["POST"]


def _log_override(
    *,
    application: Application,
    actor,
    action: str,
    previous_reviewer,
    new_reviewer,
    reason: str,
) -> HRApplicationOverrideLog:
    """Create and return an audit-log entry."""
    return HRApplicationOverrideLog.objects.create(
        application=application,
        application_pk_snapshot=application.pk,
        actor=actor,
        action=action,
        previous_reviewer=previous_reviewer,
        new_reviewer=new_reviewer,
        reason=reason or "",
    )


# ---------------------------------------------------------------------------
# Take Over Application
# ---------------------------------------------------------------------------

@login_required
@transaction.atomic
def takeover_application(request: WSGIRequest, app_id: int):
    """Re-assign an application's reviewer to the requesting user.

    The previous reviewer is preserved in the audit log.  The application
    reviewer is only changed by this explicit action – viewing the
    application does **not** trigger a takeover.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(_POST_ONLY_METHODS)

    if not can_takeover_application(request.user):
        logger.warning(
            "User %s denied takeover of application %d (insufficient permissions)",
            request.user, app_id,
        )
        messages.error(request, _("You are not authorised to take over applications."))
        return redirect("hrapplications:view", app_id)

    app = get_object_or_404(Application, pk=app_id)

    # Only pending applications can be taken over.
    if app.approved is not None:
        messages.error(
            request,
            _("This application has already been reviewed and cannot be taken over."),
        )
        return redirect("hrapplications:view", app_id)

    form = OverrideActionForm(request.POST)
    reason = ""
    if form.is_valid():
        reason = form.cleaned_data.get("reason", "")

    previous_reviewer = app.reviewer

    # Only proceed if the reviewer is actually someone else (or nobody).
    if app.reviewer == request.user:
        messages.info(request, _("You are already the reviewer of this application."))
        return redirect("hrapplications:view", app_id)

    app.reviewer = request.user
    try:
        app.reviewer_character = request.user.profile.main_character
    except Exception:  # profile may be incomplete
        app.reviewer_character = None
    app.save()

    _log_override(
        application=app,
        actor=request.user,
        action=HRApplicationOverrideLog.Action.TAKEOVER,
        previous_reviewer=previous_reviewer,
        new_reviewer=request.user,
        reason=reason,
    )

    logger.info(
        "User %s took over application %d from %s (reason: %s)",
        request.user, app_id, previous_reviewer, reason or "(none)",
    )
    notify(
        app.user,
        _("Application Taken Over"),
        message=f"Your application to {app.form.corp} is now being reviewed by {app.reviewer_str or request.user}.",
    )
    messages.success(request, _("You have taken over this application."))
    return redirect("hrapplications:view", app_id)


# ---------------------------------------------------------------------------
# Override Approve
# ---------------------------------------------------------------------------

@login_required
@transaction.atomic
def approve_override(request: WSGIRequest, app_id: int):
    """Approve a pending application regardless of who the reviewer is.

    The reviewer field is **not** changed – the original reviewer is
    preserved.  This allows a director to intervene quickly without
    altering the ownership of the application.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(_POST_ONLY_METHODS)

    if not can_approve_override(request.user):
        logger.warning(
            "User %s denied approve-override of application %d "
            "(insufficient permissions)",
            request.user, app_id,
        )
        messages.error(request, _("You are not authorised to override-approve applications."))
        return redirect("hrapplications:view", app_id)

    app = get_object_or_404(Application, pk=app_id)

    if app.approved is not None:
        messages.error(
            request,
            _("This application has already been reviewed."),
        )
        return redirect("hrapplications:view", app_id)

    form = OverrideActionForm(request.POST)
    reason = ""
    if form.is_valid():
        reason = form.cleaned_data.get("reason", "")

    previous_reviewer = app.reviewer

    app.approved = True
    app.save()

    _log_override(
        application=app,
        actor=request.user,
        action=HRApplicationOverrideLog.Action.APPROVE_OVERRIDE,
        previous_reviewer=previous_reviewer,
        new_reviewer=previous_reviewer,  # reviewer unchanged
        reason=reason,
    )

    logger.info(
        "User %s override-approved application %d (reviewer was %s, reason: %s)",
        request.user, app_id, previous_reviewer, reason or "(none)",
    )
    notify(
        app.user,
        _("Application Accepted"),
        message=f"Your application to {app.form.corp} has been approved.",
        level="success",
    )
    messages.success(request, _("Application approved via override."))
    return redirect("hrapplications:index")


# ---------------------------------------------------------------------------
# Override Reject
# ---------------------------------------------------------------------------

@login_required
@transaction.atomic
def reject_override(request: WSGIRequest, app_id: int):
    """Reject a pending application regardless of who the reviewer is.

    The reviewer field is **not** changed.  If a reason is supplied it is
    recorded in the override audit log; it does not replace the normal
    HR Applications comment mechanism.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(_POST_ONLY_METHODS)

    if not can_reject_override(request.user):
        logger.warning(
            "User %s denied reject-override of application %d "
            "(insufficient permissions)",
            request.user, app_id,
        )
        messages.error(request, _("You are not authorised to override-reject applications."))
        return redirect("hrapplications:view", app_id)

    app = get_object_or_404(Application, pk=app_id)

    if app.approved is not None:
        messages.error(
            request,
            _("This application has already been reviewed."),
        )
        return redirect("hrapplications:view", app_id)

    form = OverrideActionForm(request.POST)
    reason = ""
    if form.is_valid():
        reason = form.cleaned_data.get("reason", "")

    previous_reviewer = app.reviewer

    app.approved = False
    app.save()

    _log_override(
        application=app,
        actor=request.user,
        action=HRApplicationOverrideLog.Action.REJECT_OVERRIDE,
        previous_reviewer=previous_reviewer,
        new_reviewer=previous_reviewer,  # reviewer unchanged
        reason=reason,
    )

    logger.info(
        "User %s override-rejected application %d (reviewer was %s, reason: %s)",
        request.user, app_id, previous_reviewer, reason or "(none)",
    )
    notify(
        app.user,
        _("Application Rejected"),
        message=f"Your application to {app.form.corp} has been rejected.",
        level="danger",
    )
    messages.warning(request, _("Application rejected via override."))
    return redirect("hrapplications:index")


# ---------------------------------------------------------------------------
# Audit Log Views
# ---------------------------------------------------------------------------

@login_required
@permission_required("aa_hr_override.override_application")
def audit_log(request: WSGIRequest):
    """Show the full override audit trail.

    Visible to any user who holds the override permission (or a
    superuser, who implicitly has all permissions).
    """
    logs = (
        HRApplicationOverrideLog.objects
        .select_related("actor", "previous_reviewer", "new_reviewer")
        .all()
    )
    context = {
        "logs": logs,
        "app_id_filter": None,
    }
    return render(request, "aa_hr_override/audit_log.html", context=context)


@login_required
@permission_required("aa_hr_override.override_application")
def audit_log_for_application(request: WSGIRequest, app_id: int):
    """Show the override audit trail for a single application."""
    logs = (
        HRApplicationOverrideLog.objects
        .select_related("actor", "previous_reviewer", "new_reviewer")
        .filter(application_pk_snapshot=app_id)
        .all()
    )
    context = {
        "logs": logs,
        "app_id_filter": app_id,
    }
    return render(request, "aa_hr_override/audit_log.html", context=context)
