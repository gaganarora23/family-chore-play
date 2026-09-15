from django.contrib import admin

from .models import ChoreDefinition, FamilyMember, Household

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
