from django.core.management.base import BaseCommand

from chores.dates import household_today
from chores.models import ChoreDefinition, ChoreInstance


def recurrence_matches(recurrence_rule, date):
    """Whether a `ChoreDefinition.recurrence_rule` covers the given date.

    Grammar this command defines and consumes (#7 only stores the field
    as free text; this is the first task that gives it meaning):

    - `"daily"` -- matches every day.
    - `"weekly:<weekday>"` -- matches once a week, where `<weekday>` is a
      lowercase English weekday name (`monday`, ..., `sunday`).

    Anything else (including blank, handled by the caller) matches
    nothing.
    """
    if recurrence_rule == 'daily':
        return True
    if recurrence_rule.startswith('weekly:'):
        weekday = recurrence_rule.split(':', 1)[1]
        return date.strftime('%A').lower() == weekday
    return False


class Command(BaseCommand):
    help = (
        "Create today's ChoreInstance for each active ChoreDefinition whose "
        "recurrence_rule matches today (household-local date)."
    )

    def handle(self, *args, **options):
        created_count = 0
        definitions = ChoreDefinition.objects.filter(is_active=True).exclude(
            recurrence_rule=''
        )
        for definition in definitions:
            today = household_today(definition.household)
            if not recurrence_matches(definition.recurrence_rule, today):
                continue
            claimed_by = None
            if definition.ownership_type == ChoreDefinition.OwnershipType.ASSIGNED:
                claimed_by = definition.assigned_member
            # (chore_definition, date) is DB-uniqueness-constrained (#8), so
            # this is the actual guarantee against duplicates -- not just
            # this in-command check -- even under concurrent runs.
            _, created = ChoreInstance.objects.get_or_create(
                chore_definition=definition,
                date=today,
                defaults={'claimed_by': claimed_by},
            )
            if created:
                created_count += 1
        self.stdout.write(f'Created {created_count} chore instance(s).')
