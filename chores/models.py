from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Household(models.Model):
    """A family/household that scopes members, chores, and everything else."""

    MIN_MEMBERS = 2

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

    def delete(self, *args, **kwargs):
        """Reject a removal that would leave the household under-staffed.

        This is an application-level check, not a database constraint: a
        household can still exist with fewer than `Household.MIN_MEMBERS`
        members (e.g. mid-setup, before the second member has been added),
        it just can't be reduced below that floor by removing a member.
        """
        remaining = self.household.members.exclude(pk=self.pk).count()
        if remaining < Household.MIN_MEMBERS:
            raise ValidationError(
                f'A household must have at least {Household.MIN_MEMBERS} '
                f'members; removing {self} would leave {remaining}.'
            )
        return super().delete(*args, **kwargs)
