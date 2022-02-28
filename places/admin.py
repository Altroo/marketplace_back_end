from django.contrib import admin
from django.forms import ModelForm
from places.base.models import Country, City


class PlacesBaseAdminMixin:
    list_display = (
        'pk',
        'name',
        'name_en',
        'name_fr',
        'name_ar',
    )
    search_fields = (
        'name',
        'name_en',
        'name_fr',
        'name_ar',
    )
    list_display_links = (
        'pk',
        'name',
        'name_en',
        'name_fr',
        'name_ar',
    )


class CountryAdminForm(ModelForm):
    class Meta:
        model = Country
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        country_queryset = self.fields['parent'].queryset
        self.fields['parent'].queryset = country_queryset \
            .filter(cities__isnull=False) \
            .order_by('name', 'name_en', 'name_fr', 'name_ar').distinct()


@admin.register(Country)
class CountryAdmin(PlacesBaseAdminMixin, admin.ModelAdmin):
    list_display = PlacesBaseAdminMixin.list_display + ('currency', 'currency_ar', 'code', 'type', 'parent',)
    list_display_links = PlacesBaseAdminMixin.list_display_links + ('code', 'type', 'parent')
    search_fields = PlacesBaseAdminMixin.search_fields + ('code',)
    form = CountryAdminForm


@admin.register(City)
class CityAdmin(PlacesBaseAdminMixin, admin.ModelAdmin):
    list_display = PlacesBaseAdminMixin.list_display + ('country', 'latitude', 'longitude',)
    search_fields = PlacesBaseAdminMixin.search_fields + ('country__name_en',
                                                          'country__name_fr',
                                                          'country__name_ar',)
