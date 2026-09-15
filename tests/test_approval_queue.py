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
def parent(household):
    user = User.objects.create_user(username='parent', password='pw')
    return FamilyMember.objects.create(
        user=user, household=household, role=FamilyMember.Role.PARENT
    )


@pytest.fixture
def other_parent(other_household):
    user = User.objects.create_user(username='other-parent', password='pw')
    return FamilyMember.objects.create(
        user=user, household=other_household, role=FamilyMember.Role.PARENT
    )


@pytest.fixture
def member(household):
    user = User.objects.create_user(username='kid', password='pw')
    return FamilyMember.objects.create(
        user=user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )


def make_pending_instance(household, member, points=20):
    definition = ChoreDefinition(
        household=household,
        name='Vacuum',
        points=points,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        verification_mode=ChoreDefinition.VerificationMode.APPROVAL,
    )
    definition.full_clean()
    definition.save()
    return ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.PENDING_APPROVAL,
        claimed_by=member,
    )


@pytest.mark.django_db
def test_approving_awards_points_and_updates_status(client, household, parent, member):
    instance = make_pending_instance(household, member, points=20)
    client.force_login(parent.user)

    response = client.post(f'/instances/{instance.pk}/approve/')

    assert response.status_code == 200
    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.COMPLETED
    completion = Completion.objects.get()
    assert completion.chore_instance == instance
    assert completion.family_member == member
    assert completion.points_awarded == 20


@pytest.mark.django_db
def test_approving_twice_does_not_double_award_points(client, household, parent, member):
    instance = make_pending_instance(household, member)
    client.force_login(parent.user)

    first = client.post(f'/instances/{instance.pk}/approve/')
    second = client.post(f'/instances/{instance.pk}/approve/')

    assert first.status_code == 200
    assert second.status_code == 409
    assert Completion.objects.count() == 1


@pytest.mark.django_db
def test_non_parent_cannot_approve(client, household, member):
    instance = make_pending_instance(household, member)
    client.force_login(member.user)

    response = client.post(f'/instances/{instance.pk}/approve/')

    assert response.status_code == 403
    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.PENDING_APPROVAL
    assert Completion.objects.count() == 0


@pytest.mark.django_db
def test_non_parent_cannot_access_approval_queue(client, household, member):
    client.force_login(member.user)

    response = client.get('/approvals/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_parent_from_different_household_cannot_approve(
    client, household, member, other_parent
):
    instance = make_pending_instance(household, member)
    client.force_login(other_parent.user)

    response = client.post(f'/instances/{instance.pk}/approve/')

    assert response.status_code == 404
    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.PENDING_APPROVAL


@pytest.mark.django_db
def test_parent_only_sees_their_own_households_pending_instances(
    client, household, other_household, parent, member
):
    own_instance = make_pending_instance(household, member)
    other_user = User.objects.create_user(username='other-kid', password='pw')
    other_member = FamilyMember.objects.create(
        user=other_user, household=other_household, role=FamilyMember.Role.FAMILY_MEMBER
    )
    make_pending_instance(other_household, other_member)
    client.force_login(parent.user)

    response = client.get('/approvals/')

    instances = list(response.context['instances'])
    assert instances == [own_instance]
