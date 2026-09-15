from django import forms

from .models import ChoreDefinition, FamilyMember, Reward


class ChoreDefinitionForm(forms.ModelForm):
    """Create/edit a ChoreDefinition, scoped to a single household.

    `household` is set by the view (the logged-in parent's own household),
    never picked from the form -- see issue #9.
    """

    class Meta:
        model = ChoreDefinition
        fields = [
            'name',
            'points',
            'ownership_type',
            'assigned_member',
            'recurrence_rule',
            'verification_mode',
        ]

    def __init__(self, *args, household, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.household = household
        self.fields['assigned_member'].queryset = FamilyMember.objects.filter(
            household=household
        )
        self.fields['assigned_member'].required = False


class RewardForm(forms.ModelForm):
    """Create a Reward, scoped to a single household (view-assigned, per #9)."""

    class Meta:
        model = Reward
        fields = ['name', 'description', 'point_threshold', 'streak_threshold']

    def __init__(self, *args, household, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.household = household
        self.fields['point_threshold'].required = False
        self.fields['streak_threshold'].required = False
