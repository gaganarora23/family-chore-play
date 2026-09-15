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
def family_member(household):
    user = User.objects.create_user(username='kid', password='pw')
    return FamilyMember.objects.create(
        user=user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )


VALID_PAYLOAD = {
    'name': 'Vacuum',
    'points': 20,
    'ownership_type': ChoreDefinition.OwnershipType.CLAIMABLE,
    'assigned_member': '',
    'recurrence_rule': '',
    'verification_mode': ChoreDefinition.VerificationMode.INSTANT,
}


@pytest.mark.django_db
def test_parent_can_successfully_create_a_chore(client, parent):
    client.force_login(parent.user)

    response = client.post('/chores/new/', VALID_PAYLOAD)

    assert response.status_code == 302
    assert ChoreDefinition.objects.filter(name='Vacuum').exists()


@pytest.mark.django_db
def test_created_chore_is_attached_to_creating_parents_household(
    client, parent, other_household
):
    client.force_login(parent.user)

    client.post('/chores/new/', VALID_PAYLOAD)

    chore = ChoreDefinition.objects.get(name='Vacuum')
    assert chore.household == parent.household
    assert chore.household != other_household


@pytest.mark.django_db
def test_invalid_form_reshows_form_with_errors_and_creates_nothing(client, parent):
    client.force_login(parent.user)
    payload = dict(
        VALID_PAYLOAD,
        ownership_type=ChoreDefinition.OwnershipType.ASSIGNED,
        assigned_member='',
    )

    response = client.post('/chores/new/', payload)

    assert response.status_code == 200
    assert not ChoreDefinition.objects.exists()


@pytest.mark.django_db
def test_invalid_points_reshows_form_with_errors_and_creates_nothing(
    client, parent
):
    client.force_login(parent.user)
    payload = dict(VALID_PAYLOAD, points=0)

    response = client.post('/chores/new/', payload)

    assert response.status_code == 200
    assert not ChoreDefinition.objects.exists()


@pytest.mark.django_db
def test_non_parent_cannot_access_the_view(client, family_member):
    client.force_login(family_member.user)

    get_response = client.get('/chores/new/')
    post_response = client.post('/chores/new/', VALID_PAYLOAD)

    assert get_response.status_code == 403
    assert post_response.status_code == 403
    assert not ChoreDefinition.objects.exists()


@pytest.mark.django_db
def test_logged_out_request_redirects_to_login(client):
    response = client.get('/chores/new/')

    assert response.status_code == 302
    assert response.url.startswith('/login/')
