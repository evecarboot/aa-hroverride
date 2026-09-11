# HR Application Override

> **Proprietary — Closed Source.** You may install and use this plugin on
> Alliance Auth instances you own or operate. You may not fork,
> redistribute, or create derivative works for distribution. See
> [LICENSE](LICENSE) for full terms.

A production-ready [Alliance Auth](https://gitlab.com/allianceauth/allianceauth)
plugin that adds a **Director / CEO override layer** to the built-in
`allianceauth.hrapplications` system.

When an HR recruiter takes an application and then becomes unavailable,
forgets, or simply doesn't finish reviewing it, a Director or CEO can
intervene **without needing Django superuser access**.  The plugin
introduces a single narrow, explicit permission —
`aa_hr_override.override_application` — that lets authorised users:

- **Take Over** an application (re-assign the reviewer to themselves)
- **Approve Anyway** (approve without taking ownership)
- **Reject Anyway** (reject without taking ownership)

Every override action is recorded in a permanent **audit log** with the
actor, previous/new reviewer, optional reason, and timestamp.

---

## Requirements

| Component           | Version          |
|---------------------|------------------|
| Alliance Auth       | 5.x (tested 5.2) |
| Python              | 3.10 – 3.14      |
| `hrapplications` app| enabled          |

The built-in `allianceauth.hrapplications` app **must** be installed and
enabled — this plugin extends it; it does not replace it.

---

## Installation

### 1. Install the package

```bash
pip install aa-hr-override
```

### 2. Add to `INSTALLED_APPS`

In your `local.py` (or equivalent settings file), add **both** apps. The
ordering is critical: `aa_hr_override` **must come before**
`allianceauth.hrapplications` so that Django's template loader picks up
the plugin's override of `hrapplications/view.html`.

```python
# myauth/settings/local.py

INSTALLED_APPS += [
    "aa_hr_override",               # <-- must be BEFORE hrapplications
    "allianceauth.hrapplications",
]
```

> **Why the ordering matters:** Django's `APP_DIRS` template loader
> searches apps in `INSTALLED_APPS` order.  The plugin ships a copy of
> `hrapplications/view.html` (with override buttons added) that must be
> found *before* the original in `allianceauth.hrapplications`.

### 3. Run migrations

```bash
python manage.py migrate aa_hr_override
```

This creates the `HRApplicationOverrideLog` table and the
`aa_hr_override.override_application` permission.

### 4. Restart Alliance Auth

```bash
docker compose restart
```

(or however you restart your AA deployment)

---

## Permission Configuration

### The override permission

| Permission                                | Description                                          |
|-------------------------------------------|------------------------------------------------------|
| `aa_hr_override.override_application`     | Can override HR application reviewer restrictions     |

Assign this permission to the groups that should be able to override
applications — e.g. **HR Directors**, **CEO**, **Senior HR**.

Normal recruiters should **NOT** receive this permission.

### Required permission combinations

The override permission **does not replace** normal HR permissions. A
Director must still have the standard HR Applications permissions to
access the system.  The full combinations are:

| Action           | Required permissions                                                                 |
|------------------|--------------------------------------------------------------------------------------|
| View applications| `auth.human_resources` (standard AA — needed to see the HR view at all)             |
| Take Over        | `auth.human_resources` + `aa_hr_override.override_application`                     |
| Approve Anyway   | `auth.human_resources` + `hrapplications.approve_application` + `aa_hr_override.override_application` |
| Reject Anyway    | `auth.human_resources` + `hrapplications.reject_application` + `aa_hr_override.override_application` |
| View Audit Log   | `aa_hr_override.override_application`                                                |

Superusers automatically satisfy all permission checks (Django gives
superusers every permission) and continue to work exactly as before.

### Example group setup

Create a group called **HR Directors** and assign:

```
auth.human_resources
hrapplications.approve_application
hrapplications.reject_application
hrapplications.delete_application
hrapplications.add_applicationcomment
aa_hr_override.override_application
```

---

## Features

### 1. Take Over Application

A Director can re-assign an application's reviewer from the current
recruiter to themselves with an explicit **Take Over Application**
button.  This is an intentional action — viewing an application does
**not** trigger a takeover.

### 2. Override Approve / Override Reject

A Director can approve or reject a pending application **without**
changing the reviewer.  This preserves who originally handled the
application while letting senior staff intervene quickly.

### 3. Audit Trail

Every override action is recorded in `HRApplicationOverrideLog` with:

- Application reference (FK + ID snapshot — survives application deletion)
- Actor (who performed the override)
- Previous reviewer
- New reviewer (for takeovers)
- Action type (`TAKEOVER`, `APPROVE_OVERRIDE`, `REJECT_OVERRIDE`)
- Optional reason
- Timestamp

Audit entries are **never** deleted when the underlying application or
a referenced user is removed (all FKs use `SET_NULL`).  The log is
viewable via a sidebar menu item ("HR Override Log") and in the Django
admin (read-only).

### 4. Confirmation Modals

All override actions require confirmation through Bootstrap 5 modals
that clearly explain what is about to happen and name the current
reviewer.  An optional reason field is provided in each modal.

### 5. Optional Override Reason

When performing a takeover, approval override, or rejection override,
the Director may enter a short optional reason (max 500 characters).
This is recorded in the audit log.  For rejection, this supplements
(rather than replaces) the normal HR Applications comment mechanism.

---

## Security

- **All permission checks happen server-side.** Hiding buttons in
  templates is for usability only — every endpoint independently
  verifies permissions.
- **All state-changing endpoints are POST-only.** GET requests receive
  `405 Method Not Allowed`.
- **CSRF protection** is enforced via Django's standard `{% csrf_token %}`
  in every modal form.
- **Input validation:** application IDs are validated via
  `get_object_or_404`; action validity is checked (e.g. cannot
  override an already-reviewed application); reviewer ownership is
  checked server-side, not trusted from the browser.

---

## How It Works

The plugin overrides the `hrapplications/view.html` template (via
Django's standard `APP_DIRS` template loading) to add override buttons
and confirmation modals when the current user holds the override
permission and the application is pending with a different reviewer.

The override buttons are in a self-contained partial
(`aa_hr_override/override_actions.html`) that is included in the
overridden template.  This keeps the override UI logic isolated — if
Alliance Auth updates its template, only the include position in the
override needs to be re-synced.

The plugin's own views (takeover, approve, reject, audit log) are
registered under the `/hr-override/` URL prefix via a standard AA
`UrlHook`.

### Application states

Override actions only apply to **pending** applications
(`approved is None`).  Applications that have already been approved or
rejected cannot be overridden — this matches the existing AA behaviour
where approve/reject buttons only appear for pending applications.

---

## File Structure

```
aa_hr_override/
    __init__.py
    admin.py           # Read-only admin for audit log
    apps.py
    auth_hooks.py      # URL hook + sidebar menu item
    forms.py           # OverrideActionForm (optional reason)
    helpers.py         # Centralised permission logic
    models.py          # HRApplicationOverrideLog + override permission
    urls.py
    views.py           # POST-only override endpoints + audit log views
    migrations/
        __init__.py
        0001_initial.py
    templates/
        hrapplications/
            view.html              # Override of core AA template
        aa_hr_override/
            override_actions.html   # Buttons + confirmation modals
            audit_log.html          # Audit trail view
```

---

## Centralised Permission Helpers

All permission logic is centralised in `aa_hr_override.helpers`:

```python
from aa_hr_override.helpers import (
    can_override_hr_application,   # superuser OR override perm
    can_takeover_application,      # human_resources + override
    can_approve_override,           # human_resources + approve + override
    can_reject_override,            # human_resources + reject + override
)
```

---

## Changelog

### 1.0.0

- Initial release
- Take Over, Approve Override, Reject Override actions
- Audit trail with permanent log entries
- Confirmation modals with optional reason
- Template override integrating into the existing HR Applications UI
- Sidebar menu item for the audit log
- Read-only Django admin for audit log entries

---

## License

Proprietary — All Rights Reserved. See [LICENSE](LICENSE).

This plugin is **closed source**. You may install and use it on Alliance
Auth instances you own or operate, including via Docker. You may **not**
fork, redistribute, sell, sublicense, or create derivative works for
distribution. Private configuration changes for your own deployment are
permitted.
