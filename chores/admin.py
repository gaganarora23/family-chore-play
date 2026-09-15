from django.contrib import admin

from .models import FamilyMember, Household

admin.site.register(Household)
admin.site.register(FamilyMember)
