import datetime

import pytest
from django.db import IntegrityError, transaction

from chores.models import ChoreDefinition, ChoreInstance, Household


@pytest.fixture
def household(db):
    return Household.objects.create(name='The Smiths')


@pytest.fixture
def chore_definition(household):
    definition = ChoreDefinition(
        household=household,
        name='Vacuum',
        points=20,
        ownership_type=ChoreDefinition.OwnershipType.CLAIMABLE,
        verification_mode=ChoreDefinition.VerificationMode.INSTANT,
    )
    definition.full_clean()
    definition.save()
    return definition


@pytest.mark.django_db
def test_chore_instance_can_be_created_linked_to_a_chore_definition(
    chore_definition,
):
    instance = ChoreInstance.objects.create(
        chore_definition=chore_definition, date=datetime.date(2026, 9, 14)
    )

    assert instance.chore_definition == chore_definition


@pytest.mark.django_db
def test_second_instance_for_same_definition_and_date_raises_integrity_error(
    chore_definition,
):
    date = datetime.date(2026, 9, 14)
    ChoreInstance.objects.create(chore_definition=chore_definition, date=date)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ChoreInstance.objects.create(
                chore_definition=chore_definition, date=date
            )


@pytest.mark.django_db
def test_chore_instance_defaults_to_available_status(chore_definition):
    instance = ChoreInstance.objects.create(
        chore_definition=chore_definition, date=datetime.date(2026, 9, 14)
    )

    assert instance.status == ChoreInstance.Status.AVAILABLE
