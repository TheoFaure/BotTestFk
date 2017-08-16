import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from framework.models.models import Utterance

class Command(BaseCommand):
    help = 'Compute entity robustness for each utterance'

    def handle(self, *args, **options):
        utterances = Utterance.objects.all()
        for u in utterances:
            u.update_entity_robustness()
            self.stdout.write(self.style.SUCCESS('Successfully computed entity robustnesses.'))
