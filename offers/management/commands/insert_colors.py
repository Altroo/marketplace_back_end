import sys
from django.core.management import BaseCommand
from offers.models import Colors
from csv import reader
from os import path
from django.db.utils import IntegrityError


class InsertColors:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_colors(self):
        with open(self.parent_file_dir + '/csv_data/colors.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    Colors.objects.create(code_color=row[0], name_color=row[1])
                except IntegrityError:
                    continue


class Command(BaseCommand):
    help = 'Insert Colors'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Colors.\n')
        self.insert_colors()
        sys.stdout.write('\n')

    @staticmethod
    def insert_colors():
        colors_inserter = InsertColors()
        try:
            colors_inserter.insert_colors()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
