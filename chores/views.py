from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import parent_required
from .forms import ChoreDefinitionForm


@login_required
def home(request):
    """Placeholder home page.

    Real dashboard content (today's chores, available chores, points,
    rewards) lands in later tasks -- see `_docs/tasks.md` #8-9 and
    `_docs/plan.md` #5.
    """
    return render(request, "chores/home.html")


@parent_required
def chore_create(request):
    """Let a parent create a ChoreDefinition for their own household."""
    household = request.family_member.household
    if request.method == 'POST':
        form = ChoreDefinitionForm(request.POST, household=household)
        if form.is_valid():
            form.save()
            return redirect('chore_create_success')
    else:
        form = ChoreDefinitionForm(household=household)
    return render(request, 'chores/chore_form.html', {'form': form})


@parent_required
def chore_create_success(request):
    """Confirmation page after creating a chore.

    A real listing view lands in #10; this is the minimal "confirmation
    or listing page" the issue's acceptance criteria call for.
    """
    return render(request, 'chores/chore_create_success.html')
