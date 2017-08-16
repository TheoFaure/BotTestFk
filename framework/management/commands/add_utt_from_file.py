import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from framework.models.models import Utterance, Intent

class Command(BaseCommand):
    help = 'Command to add all the utterances in the database. Possible intents: ' \
           'add, find, edit, delete, check'

    def add_arguments(self, parser):
        parser.add_argument('intent_file', nargs='+', type=str)

    def handle(self, *args, **options):
        list_intent_file = options['intent_file']
        name_to_intent = {'add': Intent.objects.get(action="Add"),
                          'find': Intent.objects.get(action="Find"),
                          'edit': Intent.objects.get(action="Edit"),
                          'delete': Intent.objects.get(action="Delete"),
                          'check': Intent.objects.get(action="CheckAvailability")}
        for intent_file in list_intent_file:
            with open(os.path.join(settings.BASE_DIR,
                                   'framework/static/framework/feed_base/'+intent_file),
                      'r') as file:
                nb_added = 0
                for line in file:
                    try:
                        expected_intent = name_to_intent[intent_file]
                    except Utterance.DoesNotExist:
                        raise CommandError('Intent "%s" does not exist' % intent_file)

                    if Utterance.objects.filter(sentence__exact=line).count() == 0:
                        u = Utterance(sentence=line, expected_intent=expected_intent)
                        u.save()
                        nb_added += 1

                self.stdout.write(self.style.SUCCESS('Successfully added utterances for intent "%s". %s sentences added.' % (intent_file, nb_added)))
