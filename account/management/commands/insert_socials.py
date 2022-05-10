import sys
from allauth.socialaccount.models import SocialApp
# from django.contrib.sites.models import Site
from django.core.management import BaseCommand
from csv import reader
from os import path
# from django.db.utils import IntegrityError
from decouple import config


class InsertSocials:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_socials(self):
        # with open(self.parent_file_dir + '/csv_data/sites.csv', 'r+', encoding='UTF8') as site_file:
        #    sites_reader = reader(site_file, delimiter=',')
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
                    # site_file.seek(0)
                    # for site_row in sites_reader:
                    #     try:
                    #         site = Site.objects.create(domain=site_row[0], name=site_row[0])
                    #     except IntegrityError:
                    #         site = Site.objects.get(domain=site_row[0])
                    #     social.sites.add(site.pk)


class Command(BaseCommand):
    help = 'Insert Socials necessary data'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Socials.\n')
        self.insert_socials()
        sys.stdout.write('\n')

    @staticmethod
    def insert_socials():
        socials_inserter = InsertSocials()
        try:
            socials_inserter.insert_socials()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
