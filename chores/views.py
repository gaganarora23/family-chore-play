from zoneinfo import ZoneInfo

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone as django_timezone

from .models import ChoreInstance, FamilyMember


def household_today(household):
    """Today's date in the household's own timezone (plan §11: no times, just "Today")."""
    return django_timezone.now().astimezone(ZoneInfo(household.timezone)).date()


@login_required
def home(request):
    """Dashboard: today's chores that are the logged-in family member's own,
    plus the household's unclaimed claimable pool.

    "Theirs" means assigned to them or claimed by them (`claimed_by` is
    the source of truth -- see `ChoreInstance`), and still relevant today
    (`available`, `claimed`, or `pending_approval`). The available pool is
    every other today's instance that's still `available` and unclaimed
    (`claimed_by=None`) -- an assigned chore's instance, even though it's
    also `available`, has `claimed_by` already set and so belongs on the
    member's own list instead.
    """
    family_member = get_object_or_404(FamilyMember, user=request.user)
    today = household_today(family_member.household)
    today_chores = ChoreInstance.objects.filter(
        claimed_by=family_member,
        date=today,
        status__in=[
            ChoreInstance.Status.AVAILABLE,
            ChoreInstance.Status.CLAIMED,
            ChoreInstance.Status.PENDING_APPROVAL,
        ],
    ).select_related('chore_definition')
    available_chores = ChoreInstance.objects.filter(
        chore_definition__household=family_member.household,
        date=today,
        status=ChoreInstance.Status.AVAILABLE,
        claimed_by__isnull=True,
    ).select_related('chore_definition')
    return render(
        request,
        'chores/home.html',
        {'today_chores': today_chores, 'available_chores': available_chores},
    )
