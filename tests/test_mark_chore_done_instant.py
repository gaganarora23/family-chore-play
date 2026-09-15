import pytest
from django.contrib.auth import get_user_model

from chores.models import ChoreDefinition, ChoreInstance, Completion, FamilyMember, Household

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


def make_definition(household, verification_mode, points=20):
    definition = ChoreDefinition(
        household=household,
        name='Vacuum',
        points=points,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        verification_mode=verification_mode,
    )
    definition.full_clean()
    definition.save()
    return definition


@pytest.mark.django_db
def test_marking_an_instant_chore_done_awards_points_once_and_creates_one_completion(
    client, household, member
):
    definition = make_definition(
        household, ChoreDefinition.VerificationMode.INSTANT, points=20
    )
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    client.force_login(member.user)

    response = client.post(f'/instances/{instance.pk}/done/')

    assert response.status_code == 200
    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.COMPLETED
    assert Completion.objects.count() == 1
    completion = Completion.objects.get()
    assert completion.chore_instance == instance
    assert completion.family_member == member
    assert completion.points_awarded == 20


@pytest.mark.django_db
def test_calling_mark_done_twice_awards_points_only_once(client, household, member):
    definition = make_definition(household, ChoreDefinition.VerificationMode.INSTANT)
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    client.force_login(member.user)

    first = client.post(f'/instances/{instance.pk}/done/')
    second = client.post(f'/instances/{instance.pk}/done/')

    assert first.status_code == 200
    assert second.status_code == 409
    assert Completion.objects.count() == 1


@pytest.mark.django_db
def test_non_owner_cannot_mark_someone_elses_chore_done(
    client, household, member, other_member
):
    definition = make_definition(household, ChoreDefinition.VerificationMode.INSTANT)
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    client.force_login(other_member.user)

    response = client.post(f'/instances/{instance.pk}/done/')

    assert response.status_code == 403
    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.CLAIMED
    assert Completion.objects.count() == 0


@pytest.mark.django_db
def test_marking_an_approval_mode_chore_done_does_not_complete_or_award_points(
    client, household, member
):
    """Approval-mode chores go to pending_approval instead -- see #15."""
    definition = make_definition(household, ChoreDefinition.VerificationMode.APPROVAL)
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    client.force_login(member.user)

    response = client.post(f'/instances/{instance.pk}/done/')

    assert response.status_code == 200
    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.PENDING_APPROVAL
    assert Completion.objects.count() == 0


@pytest.mark.django_db
def test_get_request_is_not_allowed(client, household, member):
    definition = make_definition(household, ChoreDefinition.VerificationMode.INSTANT)
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    client.force_login(member.user)

    response = client.get(f'/instances/{instance.pk}/done/')

    assert response.status_code == 405
