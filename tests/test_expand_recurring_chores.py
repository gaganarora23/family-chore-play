import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from chores.dates import household_today
from chores.models import ChoreDefinition, ChoreInstance, FamilyMember, Household

User = get_user_model()


@pytest.fixture
def household(db):
    return Household.objects.create(name='The Smiths')


@pytest.fixture
def member(household):
    user = User.objects.create_user(username='kid')
    return FamilyMember.objects.create(
        user=user, household=household, role=FamilyMember.Role.FAMILY_MEMBER
    )


def make_definition(household, recurrence_rule, ownership_type='claimable', **overrides):
    defaults = {
        'household': household,
        'name': 'Vacuum',
        'points': 20,
        'ownership_type': ownership_type,
        'recurrence_rule': recurrence_rule,
        'verification_mode': ChoreDefinition.VerificationMode.INSTANT,
    }
    defaults.update(overrides)
    definition = ChoreDefinition(**defaults)
    definition.full_clean()
    definition.save()
    return definition


@pytest.mark.django_db
def test_running_the_command_twice_creates_no_duplicate_instances(household):
    definition = make_definition(household, 'daily')

    call_command('expand_recurring_chores')
    call_command('expand_recurring_chores')

    assert ChoreInstance.objects.filter(chore_definition=definition).count() == 1


@pytest.mark.django_db
def test_daily_chore_gets_an_instance_created_for_today(household):
    definition = make_definition(household, 'daily')

    call_command('expand_recurring_chores')

    today = household_today(household)
    instance = ChoreInstance.objects.get(chore_definition=definition)
    assert instance.date == today


@pytest.mark.django_db
def test_weekly_chore_only_gets_an_instance_on_its_matching_day(household):
    today = household_today(household)
    today_weekday = today.strftime('%A').lower()
    other_weekday = 'sunday' if today_weekday != 'sunday' else 'saturday'

    matching = make_definition(
        household, f'weekly:{today_weekday}', name='Take Out Trash'
    )
    non_matching = make_definition(
        household, f'weekly:{other_weekday}', name='Mow the Lawn'
    )

    call_command('expand_recurring_chores')

    assert ChoreInstance.objects.filter(chore_definition=matching).exists()
    assert not ChoreInstance.objects.filter(chore_definition=non_matching).exists()


@pytest.mark.django_db
def test_inactive_definition_is_skipped(household):
    definition = make_definition(household, 'daily', is_active=False)

    call_command('expand_recurring_chores')

    assert not ChoreInstance.objects.filter(chore_definition=definition).exists()


@pytest.mark.django_db
def test_blank_recurrence_rule_is_skipped(household):
    definition = make_definition(household, '')

    call_command('expand_recurring_chores')

    assert not ChoreInstance.objects.filter(chore_definition=definition).exists()


@pytest.mark.django_db
def test_assigned_chores_instance_gets_claimed_by_set_to_assigned_member(
    household, member
):
    definition = make_definition(
        household,
        'daily',
        ownership_type=ChoreDefinition.OwnershipType.ASSIGNED,
        assigned_member=member,
    )

    call_command('expand_recurring_chores')

    instance = ChoreInstance.objects.get(chore_definition=definition)
    assert instance.claimed_by == member


@pytest.mark.django_db
def test_claimable_chores_instance_has_no_claimed_by(household):
    definition = make_definition(household, 'daily')

    call_command('expand_recurring_chores')

    instance = ChoreInstance.objects.get(chore_definition=definition)
    assert instance.claimed_by is None
