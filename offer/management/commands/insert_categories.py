import sys
from django.core.management import BaseCommand
from offer.base.models import Categories
from csv import reader
from os import path
from django.db.utils import IntegrityError


class InsertCategories:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_categories(self):
        with open(self.parent_file_dir + '/csv_data/categories.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    Categories.objects.create(code_category=row[0], name_category=row[1])
                except IntegrityError:
                    continue


class Command(BaseCommand):
    help = 'Insert Categories'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Categories.\n')
        self.insert_categories()
        sys.stdout.write('\n')

    @staticmethod
    def insert_categories():
        categories_inserter = InsertCategories()
        try:
            categories_inserter.insert_categories()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
