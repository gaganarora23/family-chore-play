import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from chores.models import FamilyMember, Household

User = get_user_model()


@pytest.mark.django_db
def test_household_can_have_multiple_family_members_with_different_roles():
    household = Household.objects.create(name='The Smiths')
    parent_user = User.objects.create_user(username='parent')
    kid_user = User.objects.create_user(username='kid')

    parent = FamilyMember.objects.create(
        user=parent_user, household=household, role=FamilyMember.Role.PARENT
    )
    kid = FamilyMember.objects.create(
        user=kid_user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )

    assert set(household.members.all()) == {parent, kid}
    assert parent.role == FamilyMember.Role.PARENT
    assert kid.role == FamilyMember.Role.FAMILY_MEMBER


@pytest.mark.django_db
def test_family_members_in_different_households_are_independent():
    household_a = Household.objects.create(name='Household A')
    household_b = Household.objects.create(name='Household B')
    user_a = User.objects.create_user(username='member-a')
    user_b = User.objects.create_user(username='member-b')

    member_a = FamilyMember.objects.create(
        user=user_a, household=household_a, role=FamilyMember.Role.PARENT
    )
    FamilyMember.objects.create(
        user=user_b, household=household_b, role=FamilyMember.Role.PARENT
    )

    assert list(household_a.members.all()) == [member_a]
    assert user_b not in [member.user for member in household_a.members.all()]


@pytest.mark.django_db
def test_family_member_role_rejects_value_outside_allowed_choices():
    household = Household.objects.create(name='The Smiths')
    user = User.objects.create_user(username='someone')
    member = FamilyMember(user=user, household=household, role='sibling')

    with pytest.raises(ValidationError):
        member.full_clean()


@pytest.mark.django_db
def test_household_timezone_defaults_to_utc():
    household = Household.objects.create(name='The Smiths')

    assert household.timezone == 'UTC'
