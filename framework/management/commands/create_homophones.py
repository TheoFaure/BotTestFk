import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from framework.models.homophones import Homophone, Word

class Command(BaseCommand):
    args = ''
    help = 'Command to create the homophones in the database.'

    def _create_tags(self):
        with open(os.path.join(settings.BASE_DIR, 'framework/static/framework/homophones.txt'), 'r') as homophones:
            homoreader = csv.reader(homophones, delimiter=',', quotechar='|')
            for homo in homoreader:
                h = Homophone()
                h.save()
                for word in homo:
                    w = Word(word=word, homophone=h)
                    w.save()

    def handle(self, *args, **options):
        self._create_tags()
