import sys
from django.core.management import BaseCommand
from version.models import Version


class InsertVersion:

    @staticmethod
    def insert_version():
        version = Version.objects.all().first()
        if not version:
            Version.objects.create(current_version='1.0.0')
        else:
            print('Version object already exists !')


class Command(BaseCommand):
    help = 'Insert Version'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Version.\n')
        self.insert_version()
        sys.stdout.write('\n')

    @staticmethod
    def insert_version():
        version_inserter = InsertVersion()
        try:
            version_inserter.insert_version()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
