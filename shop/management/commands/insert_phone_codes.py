import sys
from django.core.management import BaseCommand
from shop.models import PhoneCodes
from csv import reader
from os import path
from django.db.utils import IntegrityError


class InsertPhoneCodes:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_phone_codes(self):
        with open(self.parent_file_dir + '/csv_data/phone_codes.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    PhoneCodes.objects.create(phone_code=row[0])
                except IntegrityError:
                    continue


class Command(BaseCommand):
    help = 'Insert Phone codes'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Phone codes.\n')
        self.insert_phone_codes()
        sys.stdout.write('\n')

    @staticmethod
    def insert_phone_codes():
        phone_codes_inserter = InsertPhoneCodes()
        try:
            phone_codes_inserter.insert_phone_codes()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
