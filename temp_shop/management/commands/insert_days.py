import sys
from django.core.management import BaseCommand
from auth_shop.models import Days
from csv import reader
from os import path


class InsertDays:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_days(self):
        with open(self.parent_file_dir + '/csv_data/days.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                Days.objects.create(code_day=row[0], name_day=row[1])


class Command(BaseCommand):
    help = 'Insert Days'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Days.\n')
        self.insert_days()
        sys.stdout.write('\n')

    @staticmethod
    def insert_days():
        days_inserter = InsertDays()
        try:
            days_inserter.insert_days()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
