import pytest
from django.contrib.auth import get_user_model

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


@pytest.mark.django_db
def test_dashboard_shows_streak_badge_matching_the_streak_record(
    client, household, member
):
    definition = ChoreDefinition(
        household=household,
        name='Make Bed',
        points=10,
        ownership_type=ChoreDefinition.OwnershipType.ASSIGNED,
        assigned_member=member,
        recurrence_rule='daily',
        verification_mode=ChoreDefinition.VerificationMode.INSTANT,
    )
    definition.full_clean()
    definition.save()
    today = household_today(household)
    ChoreInstance.objects.create(
        chore_definition=definition,
        date=today,
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    StreakRecord.objects.create(
        family_member=member, chore_definition=definition, current_streak=6, best_streak=6
    )
    client.force_login(member.user)

    response = client.get('/')

    content = response.content.decode()
    assert '🔥 +6' in content


@pytest.mark.django_db
def test_dashboard_shows_no_badge_when_no_streak_record_exists(
    client, household, member
):
    definition = ChoreDefinition(
        household=household,
        name='Make Bed',
        points=10,
        ownership_type=ChoreDefinition.OwnershipType.ASSIGNED,
        assigned_member=member,
        recurrence_rule='daily',
        verification_mode=ChoreDefinition.VerificationMode.INSTANT,
    )
    definition.full_clean()
    definition.save()
    today = household_today(household)
    ChoreInstance.objects.create(
        chore_definition=definition,
        date=today,
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    client.force_login(member.user)

    response = client.get('/')

    assert '🔥' not in response.content.decode()


@pytest.mark.django_db
def test_dashboard_shows_no_badge_when_streak_is_zero(client, household, member):
    definition = ChoreDefinition(
        household=household,
        name='Make Bed',
        points=10,
        ownership_type=ChoreDefinition.OwnershipType.ASSIGNED,
        assigned_member=member,
        recurrence_rule='daily',
        verification_mode=ChoreDefinition.VerificationMode.INSTANT,
    )
    definition.full_clean()
    definition.save()
    today = household_today(household)
    ChoreInstance.objects.create(
        chore_definition=definition,
        date=today,
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    StreakRecord.objects.create(
        family_member=member, chore_definition=definition, current_streak=0, best_streak=4
    )
    client.force_login(member.user)

    response = client.get('/')

    assert '🔥' not in response.content.decode()
