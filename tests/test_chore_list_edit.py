import pytest
from django.contrib.auth import get_user_model

from chores.models import ChoreDefinition, FamilyMember, Household

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
def family_member(household):
    user = User.objects.create_user(username='kid', password='pw')
    return FamilyMember.objects.create(
        user=user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )


def make_chore(household, **overrides):
    defaults = {
        'household': household,
        'name': 'Vacuum',
        'points': 20,
        'ownership_type': ChoreDefinition.OwnershipType.CLAIMABLE,
        'verification_mode': ChoreDefinition.VerificationMode.INSTANT,
    }
    defaults.update(overrides)
    chore = ChoreDefinition(**defaults)
    chore.full_clean()
    chore.save()
    return chore


@pytest.mark.django_db
def test_parent_only_sees_chores_belonging_to_their_own_household(
    client, parent, household, other_household
):
    own_chore = make_chore(household, name='Vacuum')
    make_chore(other_household, name='Mow the Lawn')
    client.force_login(parent.user)

    response = client.get('/chores/')

    chores = list(response.context['chores'])
    assert chores == [own_chore]


@pytest.mark.django_db
def test_parent_can_edit_own_households_chore(client, parent, household):
    chore = make_chore(household, name='Vacuum', points=20)
    client.force_login(parent.user)

    response = client.post(
        f'/chores/{chore.pk}/edit/',
        {
            'name': 'Vacuum Living Room',
            'points': 25,
            'ownership_type': ChoreDefinition.OwnershipType.CLAIMABLE,
            'assigned_member': '',
            'recurrence_rule': '',
            'verification_mode': ChoreDefinition.VerificationMode.INSTANT,
        },
    )

    assert response.status_code == 302
    chore.refresh_from_db()
    assert chore.name == 'Vacuum Living Room'
    assert chore.points == 25


@pytest.mark.django_db
def test_parent_cannot_open_edit_form_for_another_households_chore(
    client, parent, other_household
):
    other_chore = make_chore(other_household, name='Mow the Lawn')
    client.force_login(parent.user)

    response = client.get(f'/chores/{other_chore.pk}/edit/')

    assert response.status_code == 404


@pytest.mark.django_db
def test_parent_cannot_submit_edit_form_for_another_households_chore(
    client, parent, other_household
):
    other_chore = make_chore(other_household, name='Mow the Lawn', points=20)
    client.force_login(parent.user)

    response = client.post(
        f'/chores/{other_chore.pk}/edit/',
        {
            'name': 'Hijacked',
            'points': 1,
            'ownership_type': ChoreDefinition.OwnershipType.CLAIMABLE,
            'assigned_member': '',
            'recurrence_rule': '',
            'verification_mode': ChoreDefinition.VerificationMode.INSTANT,
        },
    )

    assert response.status_code == 404
    other_chore.refresh_from_db()
    assert other_chore.name == 'Mow the Lawn'
    assert other_chore.points == 20


@pytest.mark.django_db
def test_non_parent_cannot_access_list_view(client, family_member):
    client.force_login(family_member.user)

    response = client.get('/chores/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_non_parent_cannot_access_edit_view(client, family_member, household):
    chore = make_chore(household, name='Vacuum')
    client.force_login(family_member.user)

    get_response = client.get(f'/chores/{chore.pk}/edit/')
    post_response = client.post(f'/chores/{chore.pk}/edit/', {'name': 'Hijacked'})

    assert get_response.status_code == 403
    assert post_response.status_code == 403
