import datetime

import pytest
from django.contrib.auth import get_user_model

from chores.models import ChoreDefinition, ChoreInstance, FamilyMember, Household
from chores.views import household_today

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
def test_dashboard_shows_only_logged_in_members_chores_today(
    client, household, member, other_member
):
    today = household_today(household)
    my_definition = make_definition(
        household, 'Make Bed', ChoreDefinition.OwnershipType.ASSIGNED, member
    )
    their_definition = make_definition(
        household,
        'Feed Dog',
        ChoreDefinition.OwnershipType.ASSIGNED,
        other_member,
    )
    ChoreInstance.objects.create(
        chore_definition=my_definition, date=today, claimed_by=member
    )
    ChoreInstance.objects.create(
        chore_definition=their_definition, date=today, claimed_by=other_member
    )
    client.force_login(member.user)

    response = client.get('/')

    names = [
        instance.chore_definition.name
        for instance in response.context['today_chores']
    ]
    assert names == ['Make Bed']


@pytest.mark.django_db
def test_dashboard_does_not_show_unclaimed_pool_instances(client, household, member):
    definition = make_definition(
        household, 'Vacuum', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    today = household_today(household)
    ChoreInstance.objects.create(
        chore_definition=definition, date=today, claimed_by=None
    )
    client.force_login(member.user)

    response = client.get('/')

    assert list(response.context['today_chores']) == []


@pytest.mark.django_db
def test_dashboard_shows_empty_state_with_no_instances(client, member):
    client.force_login(member.user)

    response = client.get('/')

    assert response.status_code == 200
    assert list(response.context['today_chores']) == []
    assert 'No chores today.' in response.content.decode()


@pytest.mark.django_db
def test_dashboard_excludes_instances_not_scheduled_for_today(
    client, household, member
):
    definition = make_definition(
        household, 'Make Bed', ChoreDefinition.OwnershipType.ASSIGNED, member
    )
    yesterday = household_today(household) - datetime.timedelta(days=1)
    ChoreInstance.objects.create(
        chore_definition=definition, date=yesterday, claimed_by=member
    )
    client.force_login(member.user)

    response = client.get('/')

    assert list(response.context['today_chores']) == []


@pytest.mark.django_db
def test_logged_out_request_to_dashboard_redirects_to_login(client):
    response = client.get('/')

    assert response.status_code == 302
    assert response.url.startswith('/login/')
