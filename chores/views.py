from django.http import HttpResponse


def home(request):
    """Placeholder home page confirming the project is wired up end-to-end."""
    return HttpResponse("Family Chore Play")
