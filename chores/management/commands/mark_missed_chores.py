from django.core.management.base import BaseCommand

from chores import streaks
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
            instances = ChoreInstance.objects.filter(
                chore_definition__household=household,
                date__lt=today,
                status__in=INCOMPLETE_STATUSES,
            ).select_related('chore_definition', 'claimed_by')
            for instance in instances:
                instance.status = ChoreInstance.Status.MISSED
                instance.save(update_fields=['status'])
                if instance.claimed_by_id is not None:
                    streaks.reset_on_miss(
                        instance.claimed_by, instance.chore_definition
                    )
                missed_count += 1
        self.stdout.write(f'Marked {missed_count} chore instance(s) missed.')
