from django.contrib import admin
from .models import Version, VirementData
from django.contrib.admin import ModelAdmin


class CustomVersionAdmin(ModelAdmin):
    list_display = ('current_version', 'maintenance')

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_add_permission(self, request):
        return False


class CustomVirementData(ModelAdmin):
    list_display = ('email', 'domiciliation', 'numero_de_compte',
                    'titulaire_du_compte', 'numero_rib', 'identifiant_swift')

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(Version, CustomVersionAdmin)
admin.site.register(VirementData, CustomVirementData)
