from django.contrib import admin
from .models import Version, VirementData, NewsLetter
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


class CustomNewsLetter(ModelAdmin):
    list_display = ('email', 'created_date',)
    search_fields = ('email', )
    date_hierarchy = 'created_date'
    ordering = ('-pk',)

    def has_add_permission(self, request):
        return False


admin.site.register(Version, CustomVersionAdmin)
admin.site.register(VirementData, CustomVirementData)
admin.site.register(NewsLetter, CustomNewsLetter)
