from django.contrib import admin
from models import City
from django.contrib.admin import ModelAdmin


class CustomCitiesAdmin(ModelAdmin):
    list_display = ('pk', 'city_en', 'city_fr', 'city_ar',)
    search_fields = ('pk', 'city_en', 'city_fr', 'city_ar',)
    ordering = ('pk',)


admin.site.register(City, CustomCitiesAdmin)
