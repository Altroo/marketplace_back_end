import sys
from django.core.management import BaseCommand
from version.models import VirementData
from csv import reader
from os import path
from django.db.utils import IntegrityError


class InsertVirementData:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_virement_data(self):
        virement_data = VirementData.objects.all().first()
        if not virement_data:
            with open(self.parent_file_dir + '/csv_data/virement_data.csv', 'r+', encoding='UTF8') as f:
                csv_reader = reader(f, delimiter=',')
                for row in csv_reader:
                    try:
                        VirementData.objects.create(
                            email=row[0],
                            domiciliation=row[1],
                            numero_de_compte=row[2],
                            titulaire_du_compte=row[3],
                            numero_rib=row[4],
                            identifiant_swift=row[5],
                        )
                    except IntegrityError:
                        pass

        else:
            print('Version object already exists !')


class Command(BaseCommand):
    help = 'Insert Virement data'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Virement data.\n')
        self.insert_version()
        sys.stdout.write('\n')

    @staticmethod
    def insert_version():
        virement_inserter = InsertVirementData()
        try:
            virement_inserter.insert_virement_data()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
