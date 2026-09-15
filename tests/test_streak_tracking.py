import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from chores.dates import household_today
from chores.models import ChoreDefinition, ChoreInstance, FamilyMember, Household, StreakRecord

User = get_user_model()


@pytest.fixture
def household(db):
    return Household.objects.create(name='The Smiths')


@pytest.fixture
def member(household):
    user = User.objects.create_user(username='kid', password='pw')
    return FamilyMember.objects.create(
        user=user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )


def make_definition(household, recurrence_rule='daily', points=10):
    definition = ChoreDefinition(
        household=household,
        name='Make Bed',
        points=points,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        recurrence_rule=recurrence_rule,
        verification_mode=ChoreDefinition.VerificationMode.INSTANT,
    )
    definition.full_clean()
    definition.save()
    return definition


def make_instance(definition, date, status, claimed_by=None):
    return ChoreInstance.objects.create(
        chore_definition=definition, date=date, status=status, claimed_by=claimed_by
    )


@pytest.mark.django_db
def test_completing_a_recurring_chore_increments_current_streak_and_tracks_best(
    client, household, member
):
    definition = make_definition(household)
    today = household_today(household)
    client.force_login(member.user)

    for day_offset in range(3):
        date = today + datetime.timedelta(days=day_offset)
        instance = make_instance(
            definition, date, ChoreInstance.Status.CLAIMED, claimed_by=member
        )
        response = client.post(f'/instances/{instance.pk}/done/')
        assert response.status_code == 200

    record = StreakRecord.objects.get(family_member=member, chore_definition=definition)
    assert record.current_streak == 3
    assert record.best_streak == 3


@pytest.mark.django_db
def test_missed_instance_resets_current_streak_without_lowering_best_streak(
    client, household, member
):
    definition = make_definition(household)
    today = household_today(household)

    completed_instance = make_instance(
        definition, today, ChoreInstance.Status.CLAIMED, claimed_by=member
    )
    client.force_login(member.user)
    client.post(f'/instances/{completed_instance.pk}/done/')

    record = StreakRecord.objects.get(
        family_member=member, chore_definition=definition
    )
    assert record.current_streak == 1
    assert record.best_streak == 1

    yesterday = today - datetime.timedelta(days=1)
    make_instance(
        definition, yesterday, ChoreInstance.Status.CLAIMED, claimed_by=member
    )
    call_command('mark_missed_chores')

    record.refresh_from_db()
    assert record.current_streak == 0
    assert record.best_streak == 1


@pytest.mark.django_db
def test_one_off_chores_completion_does_not_create_a_streak_record(
    client, household, member
):
    definition = make_definition(household, recurrence_rule='')
    instance = make_instance(
        definition, '2026-09-14', ChoreInstance.Status.CLAIMED, claimed_by=member
    )
    client.force_login(member.user)

    response = client.post(f'/instances/{instance.pk}/done/')

    assert response.status_code == 200
    assert not StreakRecord.objects.filter(
        family_member=member, chore_definition=definition
    ).exists()


@pytest.mark.django_db
def test_missing_a_one_off_chore_does_not_create_a_streak_record(household, member):
    definition = make_definition(household, recurrence_rule='')
    yesterday = household_today(household) - datetime.timedelta(days=1)
    make_instance(
        definition, yesterday, ChoreInstance.Status.CLAIMED, claimed_by=member
    )

    call_command('mark_missed_chores')

    assert not StreakRecord.objects.filter(
        family_member=member, chore_definition=definition
    ).exists()


@pytest.mark.django_db
def test_approval_completion_also_increments_streak(client, household, member):
    definition = ChoreDefinition(
        household=household,
        name='Vacuum',
        points=15,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        recurrence_rule='daily',
        verification_mode=ChoreDefinition.VerificationMode.APPROVAL,
    )
    definition.full_clean()
    definition.save()
    instance = make_instance(
        definition,
        household_today(household),
        ChoreInstance.Status.PENDING_APPROVAL,
        claimed_by=member,
    )
    parent_user = User.objects.create_user(username='parent', password='pw')
    parent = FamilyMember.objects.create(
        user=parent_user, household=household, role=FamilyMember.Role.PARENT
    )
    client.force_login(parent.user)

    client.post(f'/instances/{instance.pk}/approve/')

    record = StreakRecord.objects.get(family_member=member, chore_definition=definition)
    assert record.current_streak == 1
    assert record.best_streak == 1
