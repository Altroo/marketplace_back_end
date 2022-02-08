from django.contrib import admin
from places.base.models import Cities
from django.contrib.admin import ModelAdmin


class CustomCitiesAdmin(ModelAdmin):
    list_display = ('city_en', 'city_fr', 'city_ar',)
    search_fields = ('city_en', 'city_fr', 'city_ar',)
    ordering = ('pk',)


admin.site.register(Cities, CustomCitiesAdmin)
