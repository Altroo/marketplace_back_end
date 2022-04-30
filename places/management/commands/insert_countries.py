import sys
import requests
from bs4 import BeautifulSoup
from django.core.management import BaseCommand
import re
from places.base.choices import PlaceType
from places.base.models import Country
from .updater import OverpassTurboUpdater


class CurrencyUpdater:
    """
    Get and update counrty currency
    """

    url = 'https://justforex.com/fr/education/currencies'
    currencies = {}

    def load_currencies(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        trs = soup.find(id='js-table-currencies').find('tbody').find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            if not tds or len(tds) < 4:
                continue
            currency = tds[1].getText()
            countries = tds[-1].find_all('li', {'class': re.compile('ag-flags-country_item')})
            for country in countries:
                code = country.get('class')[-1].split('-')[-1].upper()
                self.currencies.update({code: currency})

    def update_countries(self, countries):
        for country in countries:
            currency = self.currencies.get(country.code)
            if currency:
                country.currency = currency
                country.save()


class CountriesOverpassTurboUpdater(OverpassTurboUpdater):
    """
    Updating countries from Overpass Turbo
    """

    def request_headers(self):
        pass

    overpass_query = 'relation["admin_level"="2"][boundary=administrative][type!=multilinestring];out;'
    model = Country
    osm_fields_iso_prefixes = (
        'alpha2',
        'alpha3',
    )

    def get_fields_map(self):
        fields_map = super().get_fields_map()
        fields_map.update({'code': 'ISO3166-1'})
        return fields_map

    def get_osm_fields(self, osm_fields):
        osm_fields += ('ISO3166-1', 'ISO3166-1:alpha2', 'ISO3166-1:alpha3',)
        return super().get_osm_fields(osm_fields)

    def get_default(self, osm_field, item):
        if osm_field.startswith('ISO'):
            return self._get_first_not_none_value(osm_field, item, self.osm_fields_iso_prefixes, reverse=True)
        return super().get_default(osm_field, item)


class Command(BaseCommand):
    """
    Updating places from Overpass Turbo
    """

    help = 'Updating countries data'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processed.')
        CountriesOverpassTurboUpdater().update()
        self.update_currencies()
        sys.stdout.write('\n')

    @staticmethod
    def update_currencies():
        """
        Update currencies
        """
        currency_updater = CurrencyUpdater()
        currency_updater.load_currencies()
        countries = Country.objects.filter(type=PlaceType.COUNTRY)
        currency_updater.update_countries(countries)
