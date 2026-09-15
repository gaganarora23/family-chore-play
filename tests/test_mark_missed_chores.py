import datetime

import pytest
from django.core.management import call_command

from chores.dates import household_today
from chores.models import ChoreDefinition, ChoreInstance, Household


@pytest.fixture
def household(db):
    return Household.objects.create(name='The Smiths')


def make_definition(household, name='Vacuum'):
    definition = ChoreDefinition(
        household=household,
        name=name,
        points=20,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        verification_mode=ChoreDefinition.VerificationMode.INSTANT,
    )
    definition.full_clean()
    definition.save()
    return definition


def make_instance(definition, date, status):
    return ChoreInstance.objects.create(
        chore_definition=definition, date=date, status=status
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'status',
    [
        ChoreInstance.Status.AVAILABLE,
        ChoreInstance.Status.CLAIMED,
        ChoreInstance.Status.PENDING_APPROVAL,
    ],
)
def test_incomplete_prior_day_instance_is_marked_missed(household, status):
    yesterday = household_today(household) - datetime.timedelta(days=1)
    definition = make_definition(household)
    instance = make_instance(definition, yesterday, status)

    call_command('mark_missed_chores')

    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.MISSED


@pytest.mark.django_db
def test_completed_prior_day_instance_is_left_untouched(household):
    yesterday = household_today(household) - datetime.timedelta(days=1)
    definition = make_definition(household)
    instance = make_instance(
        definition, yesterday, ChoreInstance.Status.COMPLETED
    )

    call_command('mark_missed_chores')

    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.COMPLETED


@pytest.mark.django_db
def test_todays_incomplete_instance_is_left_untouched(household):
    today = household_today(household)
    definition = make_definition(household)
    instance = make_instance(definition, today, ChoreInstance.Status.AVAILABLE)

    call_command('mark_missed_chores')

    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.AVAILABLE


@pytest.mark.django_db
def test_running_the_command_twice_is_safe_and_idempotent(household):
    yesterday = household_today(household) - datetime.timedelta(days=1)
    definition = make_definition(household)
    instance = make_instance(
        definition, yesterday, ChoreInstance.Status.CLAIMED
    )

    call_command('mark_missed_chores')
    call_command('mark_missed_chores')

    instance.refresh_from_db()
    assert instance.status == ChoreInstance.Status.MISSED
