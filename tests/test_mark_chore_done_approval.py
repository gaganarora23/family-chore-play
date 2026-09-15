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


def make_approval_definition(household, points=20):
    definition = ChoreDefinition(
        household=household,
        name='Vacuum',
        points=points,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        verification_mode=ChoreDefinition.VerificationMode.APPROVAL,
    )
    definition.full_clean()
    definition.save()
    return definition


@pytest.mark.django_db
def test_submitting_an_approval_mode_chore_sets_status_to_pending_approval(
    client, household, member
):
    definition = make_approval_definition(household)
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


@pytest.mark.django_db
def test_submitting_for_approval_creates_no_completion_and_awards_no_points(
    client, household, member
):
    definition = make_approval_definition(household)
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    client.force_login(member.user)

    client.post(f'/instances/{instance.pk}/done/')

    assert Completion.objects.count() == 0


@pytest.mark.django_db
def test_points_are_not_awarded_by_this_endpoint_only_by_later_approval(
    client, household, member
):
    """#16 owns the actual approval step; this endpoint never awards points
    for an approval-mode chore, no matter how it's called."""
    definition = make_approval_definition(household, points=20)
    instance = ChoreInstance.objects.create(
        chore_definition=definition,
        date='2026-09-14',
        status=ChoreInstance.Status.CLAIMED,
        claimed_by=member,
    )
    client.force_login(member.user)

    client.post(f'/instances/{instance.pk}/done/')

    assert Completion.objects.filter(family_member=member).count() == 0
    total_points = sum(
        c.points_awarded for c in Completion.objects.filter(family_member=member)
    )
    assert total_points == 0


@pytest.mark.django_db
def test_non_owner_cannot_submit_someone_elses_approval_chore(
    client, household, member, other_member
):
    definition = make_approval_definition(household)
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


@pytest.mark.django_db
def test_submitting_an_already_pending_instance_is_a_clean_no_op(
    client, household, member
):
    definition = make_approval_definition(household)
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
    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.PENDING_APPROVAL
    assert Completion.objects.count() == 0
