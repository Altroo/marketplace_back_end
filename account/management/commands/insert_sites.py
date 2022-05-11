import sys
from django.contrib.sites.models import Site
from django.core.management import BaseCommand
from csv import reader
from os import path
from django.db.utils import IntegrityError


class AlterInsertSites:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def alter_insert_sites(self):
        with open(self.parent_file_dir + '/csv_data/sites.csv', 'r+', encoding='UTF8') as site_file:
            sites_reader = reader(site_file, delimiter=',')
            for site_row in sites_reader:
                try:
                    check_example = Site.objects.get(domain='example.com')
                    check_example.domain = site_row[0]
                    check_example.name = site_row[0]
                    check_example.save()
                    print("example.com Site updated to {}".format(site_row[0]))
                    continue
                except Site.DoesNotExist:
                    try:
                        Site.objects.create(domain=site_row[0], name=site_row[0])
                    except IntegrityError:
                        print("Site {} already exists.".format(site_row[0]))


class Command(BaseCommand):
    help = 'Alter/Insert site necessary data'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Sites.\n')
        self.insert_socials()
        sys.stdout.write('\n')

    @staticmethod
    def insert_socials():
        sites_alter_insert = AlterInsertSites()
        try:
            sites_alter_insert.alter_insert_sites()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
