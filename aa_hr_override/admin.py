"""Django admin registration for the override audit log."""

from django.contrib import admin

from .models import HRApplicationOverrideLog


@admin.register(HRApplicationOverrideLog)
class HRApplicationOverrideLogAdmin(admin.ModelAdmin):
    list_display = (
        "application_pk_snapshot",
        "action",
        "actor",
        "previous_reviewer",
        "new_reviewer",
        "timestamp",
    )
    list_filter = ("action", "timestamp")
    search_fields = (
        "application_pk_snapshot",
        "reason",
        "actor__username",
    )
    readonly_fields = (
        "application",
        "application_pk_snapshot",
        "actor",
        "previous_reviewer",
        "new_reviewer",
        "action",
        "reason",
        "timestamp",
    )
    ordering = ("-timestamp",)

    # Audit entries must never be added or deleted from the admin.
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
