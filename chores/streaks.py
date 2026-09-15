"""Streak bookkeeping (#19), called explicitly from the completion/miss
call sites rather than via Django signals -- the transactional pattern
those views/commands already use (lock, re-check, act) makes an inline
call easier to reason about than a signal handler firing outside that
transaction. #20/#22 should read `StreakRecord.current_streak` /
`best_streak` directly rather than recomputing a streak from history.
"""

from .models import StreakRecord


def record_completion(family_member, chore_definition):
    """Increment the streak for a completion. No-op for a one-off chore."""
    if not chore_definition.recurrence_rule:
        return
    record, _ = StreakRecord.objects.get_or_create(
        family_member=family_member, chore_definition=chore_definition
    )
    record.current_streak += 1
    if record.current_streak > record.best_streak:
        record.best_streak = record.current_streak
    record.save(update_fields=['current_streak', 'best_streak'])


def reset_on_miss(family_member, chore_definition):
    """Reset current_streak to 0 for a missed instance. best_streak is kept.

    A no-op if no StreakRecord exists yet (e.g. a one-off chore, or a
    member who never completed this chore before) -- missing a chore you
    never had a streak on doesn't create a record just to zero it.
    """
    StreakRecord.objects.filter(
        family_member=family_member, chore_definition=chore_definition
    ).update(current_streak=0)
