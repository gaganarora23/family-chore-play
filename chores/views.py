from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import rewards, streaks
from .dates import household_today
from .decorators import parent_required
from .forms import ChoreDefinitionForm, RewardForm
from .models import (
    ChoreDefinition,
    ChoreInstance,
    Completion,
    FamilyMember,
    Reward,
    StreakRecord,
)


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
    today_chores = list(
        ChoreInstance.objects.filter(
            claimed_by=family_member,
            date=today,
            status__in=[
                ChoreInstance.Status.AVAILABLE,
                ChoreInstance.Status.CLAIMED,
                ChoreInstance.Status.PENDING_APPROVAL,
            ],
        ).select_related('chore_definition')
    )
    available_chores = ChoreInstance.objects.filter(
        chore_definition__household=family_member.household,
        date=today,
        status=ChoreInstance.Status.AVAILABLE,
        claimed_by__isnull=True,
    ).select_related('chore_definition')
    streak_by_definition_id = dict(
        StreakRecord.objects.filter(
            family_member=family_member, current_streak__gt=0
        ).values_list('chore_definition_id', 'current_streak')
    )
    for instance in today_chores:
        instance.current_streak = streak_by_definition_id.get(
            instance.chore_definition_id
        )
    reward_progress = rewards.reward_progress_for(family_member)
    points_summary = [
        {'member': household_member, 'total_points': household_member.total_points()}
        for household_member in FamilyMember.objects.filter(
            household=family_member.household
        ).select_related('user')
    ]
    return render(
        request,
        'chores/home.html',
        {
            'today_chores': today_chores,
            'available_chores': available_chores,
            'reward_progress': reward_progress,
            'points_summary': points_summary,
        },
    )


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
    """Mark a ChoreInstance done: instant chores complete immediately and
    award points; approval-mode chores go to pending_approval instead,
    awarding nothing until a parent approves (#16).

    Only the instance's claimed_by can mark it done. Re-checks status
    (and verification mode) inside a locked transaction, same pattern as
    claiming (#13), so a double submission can't award points twice or
    re-submit an instance already pending approval.
    """
    family_member = get_object_or_404(FamilyMember, user=request.user)
    instance = get_object_or_404(ChoreInstance, pk=pk)
    if instance.claimed_by_id != family_member.id:
        raise PermissionDenied
    with transaction.atomic():
        instance = ChoreInstance.objects.select_for_update().get(pk=instance.pk)
        actionable = instance.status in (
            ChoreInstance.Status.AVAILABLE,
            ChoreInstance.Status.CLAIMED,
        )
        verification_mode = instance.chore_definition.verification_mode
        if actionable and verification_mode == ChoreDefinition.VerificationMode.INSTANT:
            instance.status = ChoreInstance.Status.COMPLETED
            instance.save(update_fields=['status'])
            Completion.objects.create(
                chore_instance=instance,
                family_member=family_member,
                points_awarded=instance.chore_definition.points,
            )
            streaks.record_completion(family_member, instance.chore_definition)
        elif (
            actionable
            and verification_mode == ChoreDefinition.VerificationMode.APPROVAL
        ):
            instance.status = ChoreInstance.Status.PENDING_APPROVAL
            instance.save(update_fields=['status'])
    return render(
        request,
        'chores/_chore_row.html',
        {'instance': instance},
        status=200 if actionable else 409,
    )


@parent_required
def chore_create(request):
    """Let a parent create a ChoreDefinition for their own household."""
    household = request.family_member.household
    if request.method == 'POST':
        form = ChoreDefinitionForm(request.POST, household=household)
        if form.is_valid():
            form.save()
            return redirect('chore_create_success')
    else:
        form = ChoreDefinitionForm(household=household)
    return render(request, 'chores/chore_form.html', {'form': form})


@parent_required
def chore_create_success(request):
    """Confirmation page after creating a chore.

    A real listing view lands in #10; this is the minimal "confirmation
    or listing page" the issue's acceptance criteria call for.
    """
    return render(request, 'chores/chore_create_success.html')


@parent_required
def chore_list(request):
    """List every ChoreDefinition belonging to the logged-in parent's household."""
    chores = ChoreDefinition.objects.filter(
        household=request.family_member.household
    )
    return render(request, 'chores/chore_list.html', {'chores': chores})


@parent_required
def chore_edit(request, pk):
    """Let a parent edit a ChoreDefinition belonging to their own household.

    A chore belonging to a different household 404s, even for a parent
    who knows/guesses its id.
    """
    household = request.family_member.household
    chore = get_object_or_404(ChoreDefinition, pk=pk, household=household)
    if request.method == 'POST':
        form = ChoreDefinitionForm(
            request.POST, instance=chore, household=household
        )
        if form.is_valid():
            form.save()
            return redirect('chore_list')
    else:
        form = ChoreDefinitionForm(instance=chore, household=household)
    return render(request, 'chores/chore_form.html', {'form': form, 'chore': chore})


@parent_required
def approval_queue(request):
    """List every ChoreInstance pending approval in the parent's household."""
    instances = ChoreInstance.objects.filter(
        chore_definition__household=request.family_member.household,
        status=ChoreInstance.Status.PENDING_APPROVAL,
    ).select_related('chore_definition', 'claimed_by__user')
    return render(request, 'chores/approval_queue.html', {'instances': instances})


@parent_required
@require_POST
def approve_completion(request, pk):
    """Approve a pending_approval ChoreInstance: complete it, record the
    Completion, and award points to claimed_by.

    Scoped to the parent's own household (404 otherwise) and re-checked
    inside a locked transaction, same idempotency pattern as #14/#15, so
    approving twice can't double-award.
    """
    instance = get_object_or_404(
        ChoreInstance,
        pk=pk,
        chore_definition__household=request.family_member.household,
    )
    with transaction.atomic():
        instance = ChoreInstance.objects.select_for_update().get(pk=instance.pk)
        approvable = instance.status == ChoreInstance.Status.PENDING_APPROVAL
        if approvable:
            instance.status = ChoreInstance.Status.COMPLETED
            instance.save(update_fields=['status'])
            Completion.objects.create(
                chore_instance=instance,
                family_member=instance.claimed_by,
                points_awarded=instance.chore_definition.points,
            )
            streaks.record_completion(instance.claimed_by, instance.chore_definition)
    return render(
        request,
        'chores/_chore_row.html',
        {'instance': instance},
        status=200 if approvable else 409,
    )


@parent_required
def reward_list(request):
    """List every Reward belonging to the logged-in parent's household."""
    household_rewards = Reward.objects.filter(household=request.family_member.household)
    return render(request, 'chores/reward_list.html', {'rewards': household_rewards})


@parent_required
def reward_create(request):
    """Let a parent create a Reward for their own household."""
    household = request.family_member.household
    if request.method == 'POST':
        form = RewardForm(request.POST, household=household)
        if form.is_valid():
            form.save()
            return redirect('reward_list')
    else:
        form = RewardForm(household=household)
    return render(request, 'chores/reward_form.html', {'form': form})
