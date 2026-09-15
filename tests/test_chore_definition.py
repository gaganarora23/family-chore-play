import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from chores.models import ChoreDefinition, FamilyMember, Household

User = get_user_model()


@pytest.fixture
def household(db):
    return Household.objects.create(name='The Smiths')


@pytest.fixture
def family_member(household):
    user = User.objects.create_user(username='kid')
    return FamilyMember.objects.create(
        user=user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )


def make_definition(household, **overrides):
    defaults = {
        'household': household,
        'name': 'Vacuum',
        'points': 20,
        'ownership_type': ChoreDefinition.OwnershipType.CLAIMABLE,
        'verification_mode': ChoreDefinition.VerificationMode.INSTANT,
    }
    defaults.update(overrides)
    return ChoreDefinition(**defaults)


@pytest.mark.django_db
def test_str_returns_the_chores_name(household):
    definition = make_definition(household, name='Take Out Trash')

    assert str(definition) == 'Take Out Trash'


@pytest.mark.django_db
def test_zero_points_raises_validation_error(household):
    definition = make_definition(household, points=0)

    with pytest.raises(ValidationError):
        definition.full_clean()


@pytest.mark.django_db
def test_negative_points_raises_validation_error(household):
    definition = make_definition(household, points=-5)

    with pytest.raises(ValidationError):
        definition.full_clean()


@pytest.mark.django_db
def test_assigned_chore_without_assigned_member_raises_validation_error(household):
    definition = make_definition(
        household,
        ownership_type=ChoreDefinition.OwnershipType.ASSIGNED,
        assigned_member=None,
    )

    with pytest.raises(ValidationError):
        definition.full_clean()


@pytest.mark.django_db
def test_claimable_chore_with_assigned_member_raises_validation_error(
    household, family_member
):
    definition = make_definition(
        household,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        assigned_member=family_member,
    )

    with pytest.raises(ValidationError):
        definition.full_clean()


@pytest.mark.django_db
def test_assigned_chore_with_valid_member_and_household_saves_successfully(
    household, family_member
):
    definition = make_definition(
        household,
        ownership_type=ChoreDefinition.OwnershipType.ASSIGNED,
        assigned_member=family_member,
    )

    definition.full_clean()
    definition.save()

    assert ChoreDefinition.objects.get(pk=definition.pk) == definition


@pytest.mark.django_db
def test_blank_recurrence_rule_saves_successfully_as_a_one_off_chore(household):
    definition = make_definition(household, recurrence_rule='')

    definition.full_clean()
    definition.save()

    assert ChoreDefinition.objects.get(pk=definition.pk).recurrence_rule == ''
