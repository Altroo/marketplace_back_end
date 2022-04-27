import sys
from django.core.management import BaseCommand
from offer.base.models import Categories, Colors, ServiceDays, ForWhom, Sizes
from auth_shop.base.models import AuthShopDays
from auth_shop.base.models import PhoneCodes
from csv import reader
from os import path
from django.db.utils import IntegrityError
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from decouple import config


class InsertAll:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_all(self):
        # This will ensure example.com is deleted so SITE_ID will be = 2
        Site.objects.all().delete()
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
        with open(self.parent_file_dir + '/csv_data/phone_codes.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    PhoneCodes.objects.create(phone_code=row[0])
                except IntegrityError:
                    continue
        with open(self.parent_file_dir + '/csv_data/sites.csv', 'r+', encoding='UTF8') as site_file:
            sites_reader = reader(site_file, delimiter=',')
            with open(self.parent_file_dir + '/csv_data/socials.csv', 'r+', encoding='UTF8') as social_file:
                socials_reader = reader(social_file, delimiter=',')
                for row in socials_reader:
                    try:
                        check_exist = SocialApp.objects.get(provider=row[0])
                        print("Provider {} already exists.".format(check_exist))
                        continue
                    except SocialApp.DoesNotExist:
                        if row[0] == "facebook":
                            social = SocialApp.objects.create(provider=row[0], name=row[1],
                                                              client_id=config('FACEBOOK_CLIENT_ID'),
                                                              secret=config('FACEBOOK_SECRET'),
                                                              key=row[4])
                        else:
                            social = SocialApp.objects.create(provider=row[0], name=row[1],
                                                              client_id=config('GOOGLE_CLIENT_ID'),
                                                              secret=config('GOOGLE_SECRET'),
                                                              key=row[4])
                        social.save()
                        site_file.seek(0)
                        for site_row in sites_reader:
                            try:
                                site = Site.objects.create(domain=site_row[0], name=site_row[0])
                            except IntegrityError:
                                site = Site.objects.get(domain=site_row[0])
                            social.sites.add(site.pk)


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
