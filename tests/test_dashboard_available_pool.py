import pytest
from django.contrib.auth import get_user_model

from chores.models import ChoreDefinition, ChoreInstance, FamilyMember, Household
from chores.views import household_today

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


def make_definition(household, name, ownership_type, assigned_member=None):
    definition = ChoreDefinition(
        household=household,
        name=name,
        points=10,
        ownership_type=ownership_type,
        assigned_member=assigned_member,
        verification_mode=ChoreDefinition.VerificationMode.INSTANT,
    )
    definition.full_clean()
    definition.save()
    return definition


@pytest.mark.django_db
def test_available_pool_shows_unclaimed_claimable_instance(client, household, member):
    definition = make_definition(
        household, 'Vacuum', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    today = household_today(household)
    ChoreInstance.objects.create(
        chore_definition=definition, date=today, claimed_by=None
    )
    client.force_login(member.user)

    response = client.get('/')

    names = [
        instance.chore_definition.name
        for instance in response.context['available_chores']
    ]
    assert names == ['Vacuum']


@pytest.mark.django_db
def test_available_pool_excludes_a_claimed_instance(client, household, member):
    definition = make_definition(
        household, 'Vacuum', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    today = household_today(household)
    ChoreInstance.objects.create(
        chore_definition=definition,
        date=today,
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    client.force_login(member.user)

    response = client.get('/')

    assert list(response.context['available_chores']) == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    'status',
    [ChoreInstance.Status.COMPLETED, ChoreInstance.Status.MISSED],
)
def test_available_pool_excludes_completed_or_missed_instances(
    client, household, member, status
):
    definition = make_definition(
        household, 'Vacuum', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    today = household_today(household)
    ChoreInstance.objects.create(
        chore_definition=definition, date=today, status=status, claimed_by=None
    )
    client.force_login(member.user)

    response = client.get('/')

    assert list(response.context['available_chores']) == []


@pytest.mark.django_db
def test_available_pool_excludes_an_assigned_chores_instance(
    client, household, member
):
    definition = make_definition(
        household, 'Make Bed', ChoreDefinition.OwnershipType.ASSIGNED, member
    )
    today = household_today(household)
    ChoreInstance.objects.create(
        chore_definition=definition,
        date=today,
        status=ChoreInstance.Status.AVAILABLE,
        claimed_by=member,
    )
    client.force_login(member.user)

    response = client.get('/')

    assert list(response.context['available_chores']) == []


@pytest.mark.django_db
def test_available_pool_only_shows_own_households_instances(
    client, household, other_household, member
):
    other_definition = make_definition(
        other_household, 'Mow the Lawn', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    today = household_today(household)
    ChoreInstance.objects.create(
        chore_definition=other_definition, date=today, claimed_by=None
    )
    client.force_login(member.user)

    response = client.get('/')

    assert list(response.context['available_chores']) == []
