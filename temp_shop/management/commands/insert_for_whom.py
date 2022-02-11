import sys
from django.core.management import BaseCommand
from auth_shop.models import ForWhom
from csv import reader
from os import path


class InsertForWhom:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_for_whom(self):
        with open(self.parent_file_dir + '/csv_data/for_whom.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                ForWhom.objects.create(code_for_whom=row[0], name_for_whom=row[1])


class Command(BaseCommand):
    help = 'Insert For Whom'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing For whom.\n')
        self.insert_for_whom()
        sys.stdout.write('\n')

    @staticmethod
    def insert_for_whom():
        for_whom_inserter = InsertForWhom()
        try:
            for_whom_inserter.insert_for_whom()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
