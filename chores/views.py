from django.shortcuts import render


def home(request):
    """Placeholder home page.

    Real dashboard content (today's chores, available chores, points,
    rewards) lands in later tasks -- see `_docs/tasks.md` #8-9 and
    `_docs/plan.md` #5.
    """
    return render(request, "chores/home.html")
