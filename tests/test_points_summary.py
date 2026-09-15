import pytest
from django.contrib.auth import get_user_model

from chores.models import ChoreDefinition, ChoreInstance, Completion, FamilyMember, Household

User = get_user_model()


@pytest.fixture
def household(db):
    return Household.objects.create(name='The Smiths')


@pytest.fixture
def other_household(db):
    return Household.objects.create(name='The Joneses')


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


def award_points(household, member, points):
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


@pytest.mark.django_db
def test_points_summary_totals_each_members_completions_independently(
    client, household, member, other_member
):
    award_points(household, member, 20)
    award_points(household, member, 15)
    award_points(household, other_member, 50)
    client.force_login(member.user)

    response = client.get('/')

    summary = {
        item['member']: item['total_points'] for item in response.context['points_summary']
    }
    assert summary[member] == 35
    assert summary[other_member] == 50


@pytest.mark.django_db
def test_member_with_zero_completions_shows_zero(client, household, member, other_member):
    award_points(household, member, 20)
    client.force_login(member.user)

    response = client.get('/')

    summary = {
        item['member']: item['total_points'] for item in response.context['points_summary']
    }
    assert summary[other_member] == 0


@pytest.mark.django_db
def test_points_summary_excludes_another_households_members(
    client, household, other_household, member
):
    other_user = User.objects.create_user(username='outsider', password='pw')
    outsider = FamilyMember.objects.create(
        user=other_user, household=other_household, role=FamilyMember.Role.FAMILY_MEMBER
    )
    award_points(other_household, outsider, 999)
    client.force_login(member.user)

    response = client.get('/')

    members_shown = [item['member'] for item in response.context['points_summary']]
    assert outsider not in members_shown
