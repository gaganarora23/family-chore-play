from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
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


class ChoreDefinition(models.Model):
    """The reusable template for a chore: name, points, and how it works.

    Kept separate from `ChoreInstance` (a specific day's occurrence) --
    see `_docs/architecture.md` §4.
    """

    class OwnershipType(models.TextChoices):
        ASSIGNED = 'assigned', 'Assigned'
        CLAIMABLE = 'claimable', 'Claimable'

    class VerificationMode(models.TextChoices):
        INSTANT = 'instant', 'Instant'
        APPROVAL = 'approval', 'Approval'

    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name='chore_definitions'
    )
    name = models.CharField(max_length=255)
    points = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    ownership_type = models.CharField(
        max_length=20, choices=OwnershipType.choices
    )
    assigned_member = models.ForeignKey(
        FamilyMember,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assigned_chore_definitions',
    )
    recurrence_rule = models.CharField(
        max_length=255,
        blank=True,
        help_text="e.g. 'daily', 'weekly:tuesday'. Blank means one-off.",
    )
    verification_mode = models.CharField(
        max_length=20, choices=VerificationMode.choices
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if (
            self.ownership_type == self.OwnershipType.ASSIGNED
            and self.assigned_member_id is None
        ):
            raise ValidationError(
                'An assigned chore must have an assigned_member.'
            )
        if (
            self.ownership_type == self.OwnershipType.CLAIMABLE
            and self.assigned_member_id is not None
        ):
            raise ValidationError(
                'A claimable chore must not have an assigned_member.'
            )


class ChoreInstance(models.Model):
    """One day's actual occurrence of a `ChoreDefinition`.

    This is the row that claiming, completion, and approval (#9-#13)
    operate on -- not the definition itself.

    `claimed_by` is the single source of truth for whose chore this
    instance is: for an *assigned* `chore_definition` it is set to the
    definition's `assigned_member` at creation time (creation is #17's
    responsibility, out of scope here); for a *claimable* one it starts
    `None` and is only set once a family member claims it (#13).
    """

    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        CLAIMED = 'claimed', 'Claimed'
        PENDING_APPROVAL = 'pending_approval', 'Pending approval'
        COMPLETED = 'completed', 'Completed'
        MISSED = 'missed', 'Missed'

    chore_definition = models.ForeignKey(
        ChoreDefinition, on_delete=models.CASCADE, related_name='instances'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE
    )
    claimed_by = models.ForeignKey(
        FamilyMember,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='claimed_chore_instances',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['chore_definition', 'date'],
                name='unique_chore_instance_per_definition_per_day',
            )
        ]

    def __str__(self):
        return f'{self.chore_definition} on {self.date} ({self.status})'
