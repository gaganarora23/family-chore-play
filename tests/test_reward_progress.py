import pytest
from django.contrib.auth import get_user_model

from chores.models import (
    ChoreDefinition,
    ChoreInstance,
    Completion,
    FamilyMember,
    Household,
    Reward,
    StreakRecord,
)

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


@pytest.fixture
def other_member(household):
    user = User.objects.create_user(username='sibling', password='pw')
    return FamilyMember.objects.create(
        user=user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )


def make_chore_instance_and_completion(household, member, points):
    definition = ChoreDefinition(
        household=household,
        name='Vacuum',
        points=points,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        verification_mode=ChoreDefinition.VerificationMode.INSTANT,
    )
    definition.full_clean()
    definition.save()
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.COMPLETED,
        claimed_by=member,
    )
    Completion.objects.create(
        chore_instance=instance, family_member=member, points_awarded=points
    )
    return definition


@pytest.mark.django_db
def test_dashboard_shows_progress_matching_members_points_and_streak(
    client, household, member
):
    make_chore_instance_and_completion(household, member, points=60)
    definition = ChoreDefinition(
        household=household,
        name='Make Bed',
        points=5,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        recurrence_rule='daily',
        verification_mode=ChoreDefinition.VerificationMode.INSTANT,
    )
    definition.full_clean()
    definition.save()
    StreakRecord.objects.create(
        family_member=member, chore_definition=definition, current_streak=4, best_streak=4
    )
    Reward.objects.create(
        household=household,
        name='Extra Screen Time',
        point_threshold=85,
        streak_threshold=7,
    )
    client.force_login(member.user)

    response = client.get('/')

    progress = response.context['reward_progress'][0]
    assert progress['points_progress'] == (60, 85)
    assert progress['streak_progress'] == (4, 7)
    assert progress['unlocked'] is False


@pytest.mark.django_db
def test_reward_unlocked_only_when_both_thresholds_met(client, household, member):
    make_chore_instance_and_completion(household, member, points=100)
    definition = ChoreDefinition(
        household=household,
        name='Make Bed',
        points=5,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        recurrence_rule='daily',
        verification_mode=ChoreDefinition.VerificationMode.INSTANT,
    )
    definition.full_clean()
    definition.save()
    StreakRecord.objects.create(
        family_member=member, chore_definition=definition, current_streak=2, best_streak=2
    )
    Reward.objects.create(
        household=household,
        name='Extra Screen Time',
        point_threshold=85,
        streak_threshold=7,
    )
    client.force_login(member.user)

    response = client.get('/')

    progress = response.context['reward_progress'][0]
    assert progress['unlocked'] is False


@pytest.mark.django_db
def test_reward_progress_reflects_only_the_viewing_members_own_totals(
    client, household, member, other_member
):
    make_chore_instance_and_completion(household, other_member, points=200)
    make_chore_instance_and_completion(household, member, points=10)
    Reward.objects.create(household=household, name='Dessert', point_threshold=50)
    client.force_login(member.user)

    response = client.get('/')

    progress = response.context['reward_progress'][0]
    assert progress['points_progress'] == (10, 50)
