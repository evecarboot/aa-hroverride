"""Hook into Alliance Auth.

Registers a URL prefix for the override endpoints and a sidebar menu
item for the audit-log view (visible only to users who hold the override
permission).
"""

from django.utils.translation import gettext_lazy as _

from allianceauth import hooks
from allianceauth.menu.hooks import MenuItemHook
from allianceauth.services.hooks import UrlHook

from . import urls


class HrOverrideMenuItem(MenuItemHook):
    """Sidebar entry for the override audit log."""

    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("HR Override Log"),
            "fa-solid fa-clipboard-list",
            "aa_hr_override:audit_log",
            navactive=["aa_hr_override:"],
        )

    def render(self, request):
        if request.user.has_perm("aa_hr_override.override_application"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_menu():
    return HrOverrideMenuItem()


@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, "aa_hr_override", r"^hr-override/")
