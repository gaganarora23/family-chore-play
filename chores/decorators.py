from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import FamilyMember


def parent_required(view):
    """Restrict a view to logged-in users whose FamilyMember role is parent.

    Enforced server-side, per `_docs/api.md`: never rely on a hidden link.
    An anonymous request redirects to login (via `login_required`); a
    logged-in non-parent gets a 403.
    """

    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        family_member = get_object_or_404(FamilyMember, user=request.user)
        if family_member.role != FamilyMember.Role.PARENT:
            raise PermissionDenied
        request.family_member = family_member
        return view(request, *args, **kwargs)

    return wrapped
