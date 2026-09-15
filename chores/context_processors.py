from .models import FamilyMember


def family_member(request):
    """Expose the logged-in user's FamilyMember to every template.

    Lets shared chrome (the nav bar) show parent-only links without every
    view needing to look it up and pass it explicitly -- see
    `_docs/design-system.md`'s "Roles, visually" section.
    """
    if not request.user.is_authenticated:
        return {}
    return {
        'current_family_member': FamilyMember.objects.filter(
            user=request.user
        ).first()
    }
