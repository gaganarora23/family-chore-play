from django.core.management.base import BaseCommand

from chores.dates import household_today
from chores.models import ChoreInstance, Household

INCOMPLETE_STATUSES = [
    ChoreInstance.Status.AVAILABLE,
    ChoreInstance.Status.CLAIMED,
    ChoreInstance.Status.PENDING_APPROVAL,
]


class Command(BaseCommand):
    help = (
        "Mark every prior day's incomplete ChoreInstance (available, "
        "claimed, or pending_approval) as missed. Pairs with "
        "expand_recurring_chores (#17); intended to run daily alongside it."
    )

    def handle(self, *args, **options):
        missed_count = 0
        for household in Household.objects.all():
            today = household_today(household)
            missed_count += ChoreInstance.objects.filter(
                chore_definition__household=household,
                date__lt=today,
                status__in=INCOMPLETE_STATUSES,
            ).update(status=ChoreInstance.Status.MISSED)
        self.stdout.write(f'Marked {missed_count} chore instance(s) missed.')
