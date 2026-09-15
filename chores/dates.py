from zoneinfo import ZoneInfo

from django.utils import timezone as django_timezone


def household_today(household):
    """Today's date in the household's own timezone (plan §11: no times, just "Today")."""
    return django_timezone.now().astimezone(ZoneInfo(household.timezone)).date()
