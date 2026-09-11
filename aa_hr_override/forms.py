"""Forms for the HR Application Override plugin."""

from django import forms
from django.utils.translation import gettext_lazy as _


class OverrideActionForm(forms.Form):
    """Optional reason supplied by a director when performing an override.

    The field is **not** required – the reason is purely informational and
    supplements (for rejection) any existing HR Applications comment
    mechanism rather than replacing it.
    """

    reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label=_("Reason (optional)"),
        max_length=500,
        help_text=_(
            "Briefly explain why this override is necessary. "
            "This is recorded in the audit log."
        ),
    )
