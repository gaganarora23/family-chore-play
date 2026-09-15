from django.contrib import admin

from .models import ChoreDefinition, FamilyMember, Household, Reward

admin.site.register(Household)
admin.site.register(FamilyMember)


@admin.register(ChoreDefinition)
class ChoreDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'household',
        'ownership_type',
        'points',
        'verification_mode',
        'is_active',
    )
    list_filter = ('household', 'ownership_type', 'verification_mode')


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'household', 'point_threshold', 'streak_threshold')
    list_filter = ('household',)
