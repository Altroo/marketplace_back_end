import sys
from django.core.management import BaseCommand
from csv import reader
from os import path, mkdir


class CreateFolders:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def create_folders(self):
        with open(self.parent_file_dir + '/csv_data/missing_folders.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                if not path.exists(self.parent_file_dir + '/' + row[0] + '/' + row[1]):
                    if row[0] == 'media':
                        # create folder
                        mkdir(self.parent_file_dir + '/' + row[0] + '/' + row[1])
                        continue
                    if row[0] == 'logs':
                        # create file
                        f = open(self.parent_file_dir + '/' + row[0] + '/' + row[1], "x")
                        f.close()
                        continue


class Command(BaseCommand):
    help = 'Create missing folders'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Missing folders creation.\n')
        self.create_folders()
        sys.stdout.write('\n')

    @staticmethod
    def create_folders():
        folders_creator = CreateFolders()
        try:
            folders_creator.create_folders()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
