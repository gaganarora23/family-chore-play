import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from chores.models import FamilyMember, Household, Reward

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
def member(household):
    user = User.objects.create_user(username='kid', password='pw')
    return FamilyMember.objects.create(
        user=user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )


VALID_PAYLOAD = {
    'name': 'Extra Screen Time',
    'description': '30 extra minutes',
    'point_threshold': 100,
    'streak_threshold': '',
}


@pytest.mark.django_db
def test_reward_with_neither_threshold_set_fails_validation(household):
    reward = Reward(household=household, name='Dessert')

    with pytest.raises(ValidationError):
        reward.full_clean()


@pytest.mark.django_db
def test_reward_with_only_point_threshold_is_valid(household):
    reward = Reward(household=household, name='Dessert', point_threshold=50)
    reward.full_clean()
    reward.save()
    assert Reward.objects.get(pk=reward.pk) == reward


@pytest.mark.django_db
def test_reward_with_only_streak_threshold_is_valid(household):
    reward = Reward(household=household, name='Movie Night', streak_threshold=7)
    reward.full_clean()
    reward.save()
    assert Reward.objects.get(pk=reward.pk) == reward


@pytest.mark.django_db
def test_parent_can_create_a_reward(client, parent):
    client.force_login(parent.user)

    response = client.post('/rewards/new/', VALID_PAYLOAD)

    assert response.status_code == 302
    reward = Reward.objects.get(name='Extra Screen Time')
    assert reward.household == parent.household


@pytest.mark.django_db
def test_non_parent_cannot_create_a_reward(client, member):
    client.force_login(member.user)

    get_response = client.get('/rewards/new/')
    post_response = client.post('/rewards/new/', VALID_PAYLOAD)

    assert get_response.status_code == 403
    assert post_response.status_code == 403
    assert not Reward.objects.exists()


@pytest.mark.django_db
def test_non_parent_cannot_access_reward_list(client, member):
    client.force_login(member.user)

    response = client.get('/rewards/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_parent_only_sees_their_own_households_rewards(
    client, household, other_household, parent
):
    own_reward = Reward.objects.create(
        household=household, name='Dessert', point_threshold=50
    )
    Reward.objects.create(
        household=other_household, name='Movie Night', streak_threshold=7
    )
    client.force_login(parent.user)

    response = client.get('/rewards/')

    rewards = list(response.context['rewards'])
    assert rewards == [own_reward]
