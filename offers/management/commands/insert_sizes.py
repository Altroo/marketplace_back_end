import sys
from django.core.management import BaseCommand
from offers.models import Sizes
from csv import reader
from os import path
from django.db.utils import IntegrityError


class InsertSizes:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_sizes(self):
        with open(self.parent_file_dir + '/csv_data/sizes.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    Sizes.objects.create(code_size=row[0], name_size=row[1])
                except IntegrityError:
                    continue


class Command(BaseCommand):
    help = 'Insert Sizes'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Sizes.\n')
        self.insert_sizes()
        sys.stdout.write('\n')

    @staticmethod
    def insert_sizes():
        sizes_inserter = InsertSizes()
        try:
            sizes_inserter.insert_sizes()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
