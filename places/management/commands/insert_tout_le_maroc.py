import sys
from django.core.management import BaseCommand
from django.db.utils import IntegrityError
from places.models import City, Country


class InsertToutLeMaroc:
    @staticmethod
    def insert():
        # check if already exists
        try:
            City.objects.get(name='Tout le maroc')
            print("Tout le maroc already exists.")
        except City.DoesNotExist:
            try:
                morocco = Country.objects.get(name_fr='Maroc')
                City.objects.create(
                    latitude='34,022405',
                    longitude='-6,834543',
                    name='Tout le maroc',
                    name_en='All of morocco',
                    name_fr='Tout le maroc',
                    name_ar='Tout le maroc',
                    overpass_turbo_id=299120862,
                    country=morocco,
                )
            except IntegrityError:
                print("Tout le maroc already exists.")
        try:
            City.objects.get(name='Les autres villes')
            print("Les autres villes already exists.")
        except City.DoesNotExist:
            try:
                morocco = Country.objects.get(name_fr='Maroc')
                City.objects.create(
                    latitude='34,022405',
                    longitude='-6,834543',
                    name='Les autres villes',
                    name_en='Other cities',
                    name_fr='Les autres villes',
                    name_ar='Les autres villes',
                    overpass_turbo_id=299120862,
                    country=morocco,
                )
            except IntegrityError:
                print("Les autres villes already exists.")


class Command(BaseCommand):
    help = 'Insert tout le maroc - Les autres villes necessary data'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start adding Tout le maroc - Les autres villes.\n')
        self.insert_now()
        sys.stdout.write('\n')

    @staticmethod
    def insert_now():
        insert = InsertToutLeMaroc()
        try:
            insert.insert()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
