import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from framework.models.models import Strategy

class Command(BaseCommand):
    help = 'Compute entity robustness for each utterance'

    def handle(self, *args, **options):
        strat = Strategy.objects.all()
        for s in strat:
            s.update_intent_robustness_per_strat()
            self.stdout.write(self.style.SUCCESS('Successfully computed intent robustnesses for %s.'%s))
