"""App configuration for aa_hr_override."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AaHrOverrideConfig(AppConfig):
    name = "aa_hr_override"
    label = "aa_hr_override"
    verbose_name = _("HR Application Override")

    def ready(self) -> None:
        pass
