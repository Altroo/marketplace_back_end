import sys
from django.core.management import BaseCommand
from offer.base.models import Categories, Colors, ServiceDays, ForWhom, Sizes
from auth_shop.base.models import AuthShopDays
from csv import reader
from os import path
from django.db.utils import IntegrityError


class InsertAll:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_all(self):
        with open(self.parent_file_dir + '/csv_data/categories.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    Categories.objects.create(code_category=row[0], name_category=row[1])
                except IntegrityError:
                    continue
        with open(self.parent_file_dir + '/csv_data/colors.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    Colors.objects.create(code_color=row[0], name_color=row[1])
                except IntegrityError:
                    continue
        with open(self.parent_file_dir + '/csv_data/days.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    ServiceDays.objects.create(code_day=row[0], name_day=row[1])
                    AuthShopDays.objects.create(code_day=row[0], name_day=row[1])
                except IntegrityError:
                    continue
        with open(self.parent_file_dir + '/csv_data/for_whom.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    ForWhom.objects.create(code_for_whom=row[0], name_for_whom=row[1])
                except IntegrityError:
                    continue
        with open(self.parent_file_dir + '/csv_data/sizes.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    Sizes.objects.create(code_size=row[0], name_size=row[1])
                except IntegrityError:
                    continue


class Command(BaseCommand):
    help = 'Insert All'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing All necessary data.\n')
        self.insert_all()
        sys.stdout.write('\n')

    @staticmethod
    def insert_all():
        all_inserter = InsertAll()
        try:
            all_inserter.insert_all()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
