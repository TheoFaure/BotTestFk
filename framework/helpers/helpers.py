from django.db.models import Count
from framework.models.models import Utterance, Intent, Answer

#### HELPERS ####
##########################
# Some useful helpers, to make views smaller.
##########################


def add_utterances(utterances, intent_id):
    '''To add the utterances in the database.'''
    lines = utterances.split("\r\n")

    intent = Intent.objects.get(id=intent_id)

    for line in lines:
        if Utterance.objects.filter(sentence=line).count() == 0:
            utt = Utterance(sentence=line, expected_intent=intent)
            utt.save()


def create_mutants_helper(strategy, validation, chatbot, nb):
    '''Link between the view that creates the mutants, and the method in the model to create them.'''
    utt_to_mutate = Utterance.objects.filter(
        expected_intent__application=chatbot
    )
    nb_mutants = 0
    for utt in utt_to_mutate:
        if utt.mutant_set.filter(strategy=strategy, validation=validation).count() < nb:
            nb_mutants += utt.mutate(strategy, validation, nb)

    return nb_mutants