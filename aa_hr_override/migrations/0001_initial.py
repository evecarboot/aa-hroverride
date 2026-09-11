"""Initial migration for aa_hr_override.

Creates the ``HRApplicationOverrideLog`` model and the custom
``override_application`` permission.
"""

import django.conf
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
        ("hrapplications", "0009_alter_application_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="HRApplicationOverrideLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "application_pk_snapshot",
                    models.PositiveIntegerField(
                        help_text=(
                            "Snapshot of the application PK at the time of the action."
                        ),
                        verbose_name="application ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("TAKEOVER", "Take Over"),
                            ("APPROVE_OVERRIDE", "Approve Override"),
                            ("REJECT_OVERRIDE", "Reject Override"),
                        ],
                        max_length=30,
                        verbose_name="action",
                    ),
                ),
                (
                    "reason",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text=(
                            "Optional reason provided by the director for this "
                            "override."
                        ),
                        verbose_name="reason",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(auto_now_add=True, verbose_name="timestamp"),
                ),
                (
                    "application",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="override_logs",
                        to="hrapplications.application",
                        verbose_name="application",
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="hr_override_actions",
                        to=django.conf.settings.AUTH_USER_MODEL,
                        verbose_name="actor",
                    ),
                ),
                (
                    "previous_reviewer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="hr_override_previous_reviewer",
                        to=django.conf.settings.AUTH_USER_MODEL,
                        verbose_name="previous reviewer",
                    ),
                ),
                (
                    "new_reviewer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="hr_override_new_reviewer",
                        to=django.conf.settings.AUTH_USER_MODEL,
                        verbose_name="new reviewer",
                    ),
                ),
            ],
            options={
                "verbose_name": "HR Application Override Log",
                "verbose_name_plural": "HR Application Override Logs",
                "ordering": ["-timestamp"],
                "permissions": (
                    (
                        "override_application",
                        "Can override HR application reviewer restrictions",
                    ),
                ),
            },
        ),
    ]
