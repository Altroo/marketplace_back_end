from django.contrib import admin
from .models import Version
from django.contrib.admin import ModelAdmin


class CustomVersionAdmin(ModelAdmin):
    list_display = ('current_version', 'maintenance')

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(Version, CustomVersionAdmin)
