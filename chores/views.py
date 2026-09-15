from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import ChoreDefinition, ChoreInstance, Completion, FamilyMember


@login_required
def home(request):
    """Placeholder home page.

    Real dashboard content (today's chores, available chores, points,
    rewards) lands in later tasks -- see `_docs/tasks.md` #8-9 and
    `_docs/plan.md` #5.
    """
    return render(request, "chores/home.html")


@login_required
@require_POST
def claim_chore(request, pk):
    """Let a family member claim an available, unclaimed ChoreInstance.

    Re-checks status/claimed_by inside a locked transaction so two
    simultaneous claims on the same instance can't both succeed -- the
    client's last-rendered state is never trusted. An assigned chore's
    instance already has claimed_by set at creation (#8), so it's
    rejected here the same as an already-claimed one.
    """
    family_member = get_object_or_404(FamilyMember, user=request.user)
    instance = get_object_or_404(
        ChoreInstance, pk=pk, chore_definition__household=family_member.household
    )
    with transaction.atomic():
        instance = ChoreInstance.objects.select_for_update().get(pk=instance.pk)
        claimable = (
            instance.status == ChoreInstance.Status.AVAILABLE
            and instance.claimed_by_id is None
        )
        if claimable:
            instance.status = ChoreInstance.Status.CLAIMED
            instance.claimed_by = family_member
            instance.save(update_fields=['status', 'claimed_by'])
    return render(
        request,
        'chores/_chore_row.html',
        {'instance': instance},
        status=200 if claimable else 409,
    )


@login_required
@require_POST
def mark_chore_done(request, pk):
    """Complete an instant-verification ChoreInstance and award its points.

    Only the instance's claimed_by can mark it done. Re-checks status
    (and verification mode) inside a locked transaction, same pattern as
    claiming (#13), so a double submission can't award points twice.
    An approval-mode chore is left untouched here -- that path is #15/#16.
    """
    family_member = get_object_or_404(FamilyMember, user=request.user)
    instance = get_object_or_404(ChoreInstance, pk=pk)
    if instance.claimed_by_id != family_member.id:
        raise PermissionDenied
    with transaction.atomic():
        instance = ChoreInstance.objects.select_for_update().get(pk=instance.pk)
        completable = (
            instance.status
            in (ChoreInstance.Status.AVAILABLE, ChoreInstance.Status.CLAIMED)
            and instance.chore_definition.verification_mode
            == ChoreDefinition.VerificationMode.INSTANT
        )
        if completable:
            instance.status = ChoreInstance.Status.COMPLETED
            instance.save(update_fields=['status'])
            Completion.objects.create(
                chore_instance=instance,
                family_member=family_member,
                points_awarded=instance.chore_definition.points,
            )
    return render(
        request,
        'chores/_chore_row.html',
        {'instance': instance},
        status=200 if completable else 409,
    )
