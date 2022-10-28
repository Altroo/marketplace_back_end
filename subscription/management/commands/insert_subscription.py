import sys
from django.core.management import BaseCommand
from subscription.models import AvailableSubscription
from csv import reader
from os import path
from django.db.utils import IntegrityError


class InsertSubscriptions:
    parent_file_dir = path.abspath(path.join(path.dirname(__file__), "../../.."))

    def insert_subscriptions(self):
        with open(self.parent_file_dir + '/csv_data/subscriptions.csv', 'r+', encoding='UTF8') as f:
            csv_reader = reader(f, delimiter=',')
            for row in csv_reader:
                try:
                    AvailableSubscription.objects.create(
                        nbr_article=int(row[0]),
                        prix_ht=int(row[1]),
                        prix_ttc=int(row[2]),
                        prix_unitaire_ht=int(row[3]),
                        prix_unitaire_ttc=int(row[4]),
                        pourcentage=int(row[5]),
                    )
                except IntegrityError:
                    continue


class Command(BaseCommand):
    help = 'Insert Subscriptions'

    def handle(self, *args, **options):
        sys.stdout.write(f'Start processing Subscriptions.\n')
        self.insert_subscriptions()
        sys.stdout.write('\n')

    @staticmethod
    def insert_subscriptions():
        subscription_inserter = InsertSubscriptions()
        try:
            subscription_inserter.insert_subscriptions()
        except Exception as e:
            sys.stdout.write('{}.\n'.format(e))
