"""URL configuration for the HR Application Override plugin."""

from django.urls import path

from . import views

app_name = "aa_hr_override"

urlpatterns = [
    path(
        "takeover/<int:app_id>/",
        views.takeover_application,
        name="takeover",
    ),
    path(
        "approve/<int:app_id>/",
        views.approve_override,
        name="approve_override",
    ),
    path(
        "reject/<int:app_id>/",
        views.reject_override,
        name="reject_override",
    ),
    path(
        "log/",
        views.audit_log,
        name="audit_log",
    ),
    path(
        "log/<int:app_id>/",
        views.audit_log_for_application,
        name="audit_log_for_application",
    ),
]
