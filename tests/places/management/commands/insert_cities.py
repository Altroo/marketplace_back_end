import sys
from django.core.management import BaseCommand
from models import City
from csv import reader
from os import path


class InsertCities:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_cities(self):
        with open(self.parent_file_dir + '/csv_data/cities.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                City.objects.create(city_en=row[0], city_fr=row[1], city_ar=row[2])


class Command(BaseCommand):
    help = 'Insert Cities'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Cities.\n')
        self.insert_cities()
        sys.stdout.write('\n')

    @staticmethod
    def insert_cities():
        cities_inserter = InsertCities()
        try:
            cities_inserter.insert_cities()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
