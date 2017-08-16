import json
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models.models import Utterance, Intent, Mutant, Strategy
from django.template import loader
from .forms import UploadUtterancesForm, CreateMutantsForm, GetAnsMutantsForm
from .helpers.helpers import add_utterances, create_mutants_helper


def manage_utterances(request):
    '''Route to add utterances
    :return The form to add utterances'''
    if request.method == 'POST':
        form = UploadUtterancesForm(request.POST)
        if form.is_valid():
            add_utterances(request.POST['utterances'], request.POST['intent'])
            return render(request, 'framework/manage_utterances.html', {'form': UploadUtterancesForm()}) #HttpResponseRedirect('/framework/utterance_answers/')
    else:
        form = UploadUtterancesForm()
    return render(request, 'framework/manage_utterances.html', {'form': form})


def utterance_answers(request):
    '''Route to show the page to compute answers to utterances.
    Shows the accuracy and the number of missing answers.
    :return nb of missing answers, the accuracies for each intent'''
    template = loader.get_template('framework/utterance_answers.html')
    nb_missing_answers = Utterance.objects.filter(answer_id__isnull=True).count()

    context = { "nb_missing_answers": nb_missing_answers }
    return HttpResponse(template.render(context, request))


@csrf_exempt
def compute_answers(request):
    '''Route to compute answers to the utterances.
    (hit with ajax, which is why csrf_exempt).
    :return nb of missing answers, the accuracies for each intent '''
    utt_without_ans = Utterance.objects.filter(answer_id__isnull=True)
    for utt in utt_without_ans:
        utt.compute_answer()

    nb_missing_answers = Utterance.objects.filter(answer_id__isnull=True).count()

    context = { "nb_missing_answers": nb_missing_answers }
    j = json.dumps(context)
    return HttpResponse(j)


def create_mutants(request):
    '''Route to create the mutants.
    This will create NEW mutants for the strategy selected, using the validation selected,
    for the chatbot selected.
    Nb_per_mutant is the number of mutants that will be created for each sentence.
    For example if Nb_per_mutant=5. For each utterance:
        If there already are 5 mutants for the sentence, no mutant will be created.
        If there is 1 mutant, 4 will be created.
        If there is 1 mutant, and only 1 other can be created (because the strategy selected can
           create only 1 mutant. Only 1 mutant will be created (no duplicate).
    :return The form to create mutants, the nb of mutants created, the nb of missing answers'''
    if request.method == 'POST':
        form = CreateMutantsForm(request.POST)
        if form.is_valid():
            nb_mutants = create_mutants_helper(form.cleaned_data['strategy'],
                                               form.cleaned_data['validation'],
                                               form.cleaned_data['chatbot'],
                                               form.cleaned_data['nb_per_mutant'])

            nb_missing_answers = Mutant.objects.filter(answer_id__isnull=True).count()

            return render(request, 'framework/create_mutants.html',
                          {'form': CreateMutantsForm(),
                           'nb_mutants': nb_mutants,
                           'nb_missing_answers': nb_missing_answers}) #HttpResponseRedirect('/framework/utterance_answers/')
    else:
        form = CreateMutantsForm()
    nb_missing_answers = Mutant.objects.filter(answer_id__isnull=True).count()
    return render(request, 'framework/create_mutants.html', {'form': form,
                                                             'nb_mutants': -1,
                                                             'nb_missing_answers': nb_missing_answers})


def mutants_answers(request):
    '''Compute the answers for the mutants.
    You can chose how many answers you want to create.
    :return The form to get answers to mutants, the strategies'''
    if request.method == 'POST':
        form = GetAnsMutantsForm(request.POST)
        if form.is_valid():
            strat = form.cleaned_data['strategy']
            nb = form.cleaned_data['nb_answers']

            mutants_to_compute = Mutant.objects.filter(answer_id__isnull=True, strategy=strat)[:nb]
            for mut in mutants_to_compute:
                mut.compute_answer()
                mut.utterance.update_entity_robustness()

            return render(request, 'framework/mutants_answers.html',
                          {'form': GetAnsMutantsForm(),
                           'strategies': Strategy.objects.all()})
    else:
        form = GetAnsMutantsForm()
    return render(request, 'framework/mutants_answers.html', {'form': form,
                                                             'strategies': Strategy.objects.all()})


def results_stats(request):
    '''Route to show the general results.
    Shows the robustness by intent and by strategy.
    :return the intents, the strategies'''
    template = loader.get_template('framework/results_stats.html')

    intents = Intent.objects.all()
    strategies = Strategy.objects.all()

    tab = [["", "Original"] + [i.__str__() for i in intents], ["Mutant", ""] + [Mutant.nb_mut_i_orig(i) for i in intents]]

    middle = [["", ""] + [Mutant.nb_mut_i_orig_mutated_to_i_mut(i_orig, i_mut) for i_mut in intents] for i_orig in intents]
    for line in middle:
        tab.append(line)
    tab.append(["Robustness",""] + [round(Mutant.intent_robustness_per_intent(i), 2) for i in intents])

    nb_mut = [Mutant.nb_mut_i_mut(i) for i in intents]
    for idx in range(intents.count()):
        tab[2+idx][0] = intents[idx].__str__()
        tab[2+idx][1] = nb_mut[idx]

    context = {'nb_utt_per_int': [[i.__str__(),
                                   Utterance.objects.filter(expected_intent=i).count(),
                                   Utterance.objects.filter(answer__intent=i).count(),
                                   round(Utterance.objects.filter(answer__intent=i, expected_intent=i).count()/Utterance.objects.filter(expected_intent=i).count(), 2)]
                                  for i in intents if i.id != 1],
               'general_accuracy': round(sum([Utterance.objects.filter(answer__intent=i, expected_intent=i).count()/Utterance.objects.filter(expected_intent=i).count() for i in intents if i.id != 1])/intents.count(), 2),
               'nb_utt': Utterance.objects.all().count(),
               'rob_per_strat': [[s,
                                  round(Mutant.intent_robustness_per_strat(s), 2),
                                  Mutant.objects.filter(strategy=s, answer__isnull=False).count()] for s in strategies],
               'tab': tab,
               'general_robustness': round(sum([Mutant.intent_robustness_per_intent(i) for i in intents])/intents.count(), 3)}
    return HttpResponse(template.render(context, request))


def results_detailed(request):
    '''Route to show the results detailed per utterance.
    :return The utterances.'''
    template = loader.get_template('framework/results_detailed.html')
    utt = Utterance.objects.all()
    utterances = []
    for u in utt:
        r_int = u.intent_robustness
        if r_int < 1 or u.entity_robustness < 1 :
            utterances.append([u, round(r_int, 2)])
    context = {'utterances': utterances}
    return HttpResponse(template.render(context, request))


def results_utterance(request, utterance_id):
    '''Route to the detailed results for a specific utterance.
    :return the utterance, the strategies'''
    template = loader.get_template('framework/results_utterance.html')

    utterance = Utterance.objects.get(id=utterance_id)
    possible_strategies = Strategy.objects.filter(mutant__utterance=utterance_id,
                                                  mutant__answer__isnull=False).distinct()

    context = {
        'utterance': utterance,
        'possible_strategies': possible_strategies
    }
    return HttpResponse(template.render(context, request))


def results_strategy(request, strategy_id):
    '''Route to the detailed results for a specific strategy.
    :return '''
    template = loader.get_template('framework/results_strategy.html')

    strategy = Strategy.objects.get(id=strategy_id)
    utt = Utterance.objects.filter(mutant__strategy=strategy,
                                          mutant__answer__isnull=False).distinct()
    utterances = []
    for u in utt:
        r_int = u.intent_robustness
        if r_int < 1 or u.entity_robustness < 1 :
            utterances.append([u, round(r_int, 2)])

    context = {
        'utterances': utterances,
        'strategy': strategy
    }
    return HttpResponse(template.render(context, request))


def index(request):
    '''Route to index'''
    template = loader.get_template('framework/index.html')
    context = {}
    return HttpResponse(template.render(context, request))
