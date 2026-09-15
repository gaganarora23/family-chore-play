from django.conf import settings
from django.db import models


class Household(models.Model):
    """A family/household that scopes members, chores, and everything else."""

    name = models.CharField(max_length=255)
    timezone = models.CharField(
        max_length=63,
        default='UTC',
        help_text="IANA timezone name, e.g. 'America/Los_Angeles'.",
    )

    def __str__(self):
        return self.name


class FamilyMember(models.Model):
    """A user's membership in a household, with the role they hold there."""

    class Role(models.TextChoices):
        PARENT = 'parent', 'Parent'
        FAMILY_MEMBER = 'family_member', 'Family member'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name='members'
    )
    role = models.CharField(max_length=20, choices=Role.choices)

    def __str__(self):
        return f'{self.user} ({self.role}) @ {self.household}'
