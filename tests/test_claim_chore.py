import threading

import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from django.test import Client

from chores.models import ChoreDefinition, ChoreInstance, FamilyMember, Household

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
def other_member(other_household):
    user = User.objects.create_user(username='outsider', password='pw')
    return FamilyMember.objects.create(
        user=user,
        household=other_household,
        role=FamilyMember.Role.FAMILY_MEMBER,
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
def test_uncontested_claim_succeeds(client, household, member):
    definition = make_definition(
        household, 'Vacuum', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    instance = ChoreInstance.objects.create(
        chore_definition=definition, date='2026-09-14'
    )
    client.force_login(member.user)

    response = client.post(f'/instances/{instance.pk}/claim/')

    assert response.status_code == 200
    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.CLAIMED
    assert instance.claimed_by == member


@pytest.mark.django_db
def test_claiming_an_already_claimed_instance_fails(client, household, member):
    definition = make_definition(
        household, 'Vacuum', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    client.force_login(member.user)

    response = client.post(f'/instances/{instance.pk}/claim/')

    assert response.status_code == 409
    instance.refresh_from_db()
    assert instance.claimed_by == member


@pytest.mark.django_db
def test_claiming_a_completed_instance_fails(client, household, member):
    definition = make_definition(
        household, 'Vacuum', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.COMPLETED,
        claimed_by=member,
    )
    client.force_login(member.user)

    response = client.post(f'/instances/{instance.pk}/claim/')

    assert response.status_code == 409


@pytest.mark.django_db
def test_claiming_an_assigned_chores_instance_is_rejected(client, household, member):
    definition = make_definition(
        household, 'Make Bed', ChoreDefinition.OwnershipType.ASSIGNED, member
    )
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.AVAILABLE,
        claimed_by=member,
    )
    other_user = User.objects.create_user(username='sibling', password='pw')
    sibling = FamilyMember.objects.create(
        user=other_user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )
    client.force_login(sibling.user)

    response = client.post(f'/instances/{instance.pk}/claim/')

    assert response.status_code == 409
    instance.refresh_from_db()
    assert instance.claimed_by == member


@pytest.mark.django_db
def test_member_from_another_household_cannot_claim(
    client, household, other_member
):
    definition = make_definition(
        household, 'Vacuum', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    instance = ChoreInstance.objects.create(
        chore_definition=definition, date='2026-09-14'
    )
    client.force_login(other_member.user)

    response = client.post(f'/instances/{instance.pk}/claim/')

    assert response.status_code == 404
    instance.refresh_from_db()
    assert instance.claimed_by is None


@pytest.mark.django_db
def test_get_request_is_not_allowed(client, household, member):
    definition = make_definition(
        household, 'Vacuum', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    instance = ChoreInstance.objects.create(
        chore_definition=definition, date='2026-09-14'
    )
    client.force_login(member.user)

    response = client.get(f'/instances/{instance.pk}/claim/')

    assert response.status_code == 405


@pytest.mark.django_db(transaction=True)
def test_two_simultaneous_claim_attempts_only_one_succeeds():
    household = Household.objects.create(name='The Smiths')
    definition = make_definition(
        household, 'Vacuum', ChoreDefinition.OwnershipType.CLAIMABLE
    )
    instance = ChoreInstance.objects.create(
        chore_definition=definition, date='2026-09-14'
    )
    user_a = User.objects.create_user(username='member-a', password='pw')
    member_a = FamilyMember.objects.create(
        user=user_a, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )
    user_b = User.objects.create_user(username='member-b', password='pw')
    member_b = FamilyMember.objects.create(
        user=user_b, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )

    results = {}
    barrier = threading.Barrier(2)

    def attempt(member, key):
        thread_client = Client()
        thread_client.force_login(member.user)
        barrier.wait()
        response = thread_client.post(f'/instances/{instance.pk}/claim/')
        results[key] = response.status_code
        connections.close_all()

    thread_a = threading.Thread(target=attempt, args=(member_a, 'a'))
    thread_b = threading.Thread(target=attempt, args=(member_b, 'b'))
    thread_a.start()
    thread_b.start()
    thread_a.join()
    thread_b.join()

    assert sorted(results.values()) == [200, 409]
    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.CLAIMED
    assert instance.claimed_by in {member_a, member_b}
