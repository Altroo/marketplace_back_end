import sys
import time
from django.core.management import BaseCommand
from django.db.models import Q, F, OuterRef, Exists
from places.base.models import City, Country
from .updater import OverpassTurboUpdater


class CitiesOverpassTurboUpdater(OverpassTurboUpdater):
    """
    Updating countries from Overpass Turbo
    """

    overpass_query = '''
    area(%s)->.searchArea;(node[place~"city|town"](area.searchArea););out body;>;out skel qt;
    '''
    model = City

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.place = Country.objects.filter(code=self.kwargs.get('code')).first()
        self.country = self.place if not self.place.parent else self.place.parent
        self.common_defaults = {'country': self.country}

    def get_overpass_query(self):
        area = int(self.place.overpass_turbo_id + 36e8)
        return super().get_overpass_query() % area


class Command(BaseCommand):
    """
    Updating places from Overpass Turbo
    """

    help = 'Updating country and city data'

    def add_arguments(self, parser):
        parser.add_argument('-c', '--countries', type=str, required=True, help='Official country code in English '
                                                                               'separated by semicolons')

    def handle(self, *args, **options):
        countries_codes = options.get('countries').split(';')
        for country_code in countries_codes:
            country = Country.objects.filter(code=country_code).first()

            if not country or not country.is_country:
                continue

            sys.stdout.write(f'Country being processed: {country.display_name}.')

            codes = [country_code]
            if country.children.all().exists():
                codes.extend(list(country.children.all().values_list('code', flat=True)))

            for code in codes:
                CitiesOverpassTurboUpdater(code=code).update()
                time.sleep(5)
            sys.stdout.write('\n')

            self.update_english_names_by_french(country)
            self.update_french_names_by_english(country)
            self.delete_dublicate_names(country)
            self.delete_empty_names(country)

    @staticmethod
    def update_english_names_by_french(country):
        """
        Update english names from french
        """
        country.cities.all() \
            .filter(Q(name_en__exact='') | Q(name_en__isnull=True)) \
            .update(name_en=F('name_fr'))

    @staticmethod
    def update_french_names_by_english(country):
        """
        Update french names from english
        """
        country.cities.all() \
            .filter(Q(name_fr__exact='') | Q(name_fr__isnull=True)) \
            .update(name_fr=F('name_en'))

    @staticmethod
    def delete_dublicate_names(country):
        """
        Delete dublicate names
        """
        exists_subquery = Exists(country.cities.all().filter(name=OuterRef('name')).exclude(pk=OuterRef('pk')))
        duplicate_cities = country.cities.all().annotate(dublicate_exists=exists_subquery).filter(dublicate_exists=True)

        saved_duplicate_cities = set()
        for duplicate_city in duplicate_cities:
            try:
                duplicates = duplicate_cities \
                    .filter(name=duplicate_city.name) \
                    .values('pk', 'name', 'name_en', 'name_fr', 'name_ar')
                lens = list(map(len, map(lambda city: list(filter(None, city.values())), duplicates)))
                saved_duplicate_cities.add(duplicate_cities[lens.index(max(lens))].pk)
            except Exception as e:
                pass
        duplicate_cities.exclude(pk__in=list(saved_duplicate_cities)).delete()

    @staticmethod
    def delete_empty_names(country):
        """
        Delete empty names
        """
        country.cities.all().filter(
            Q(Q(name__exact='') | Q(name__isnull=True)) &
            Q(Q(name_en__exact='') | Q(name_en__isnull=True)) &
            Q(Q(name_fr__exact='') | Q(name_fr__isnull=True)) &
            Q(Q(name_ar__exact='') | Q(name_ar__isnull=True))
        ).delete()
