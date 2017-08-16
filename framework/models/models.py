from django.db import models
from framework.helpers.api_calls import get_luis
from framework.helpers.mutation_methods import mutation_homophones, mutation_swap_letter, mutation_swap_word, mutation_random, \
    mutation_verb_at_end, mutation_w2v, mutation_glove

from framework.helpers.validation_methods import is_valid_true, is_valid_spellcheck


def get_answer(sentence):
    '''
    Method that computes the answer for the given sentence, using the API of Luis.ai
    Links the answer to the right chatbot.
    Selects the corresponding intent (or creates a new one).
    Creates the new entities corresponding.
    Saves the answer in DB.
    :param sentence: The query. Can be a mutant or an original utterance.
    :return: the answer (the object).
    '''
    luis_json = get_luis(sentence)

    try:
        intent = str(luis_json['topScoringIntent']['intent'])
    except KeyError as e:
        print("Query not valid, no top scoring intent found")
        raise e

    try:
        application, action = intent.split(".")
    except ValueError as e:
        action = "None"
        application = "default"

    entities = [(e['entity'], e['type']) for e in luis_json['entities']]

    try:
        chatbot = Chatbot.objects.get(name=application)
    except models.ObjectDoesNotExist as e:
        chatbot = Chatbot(name=application)
        chatbot.save()

    try:
        intent = Intent.objects.get(application=chatbot, action=action)
    except models.ObjectDoesNotExist as e:
        intent = Intent(application=chatbot, action=action)
        intent.save()

    answer = Answer(intent=intent)
    answer.save()

    for entity in entities:
        answer.entity.create(value=entity[0], type=entity[1])

    print("Answer computed", intent, answer.entity.all())
    return answer


class Chatbot(models.Model):
    '''The application (the name of the application on luis.ai)'''
    name = models.CharField(max_length=30)
    def __str__(self):
        return self.name


class Intent(models.Model):
    '''The intention that is detected on the utterance by luis.ai.'''
    application = models.ForeignKey(Chatbot, null=True, blank=True)
    action = models.CharField(max_length=30)
    def __str__(self):
        return "{}.{}".format(self.application, self.action)

    @property
    def nb_mut_ans(self):
        '''Property. The number of mutants that have an answer,
        and for which the answer to the utterance as this intent.'''
        return Mutant.objects.filter(utterance__answer__intent=self, answer__isnull=False).count()


class Entity(models.Model):
    '''The parameter of a query.
    An entity has a type (for example a date, a location, a contact).
    And a value (10th of october, UCD College, INSA Lyon...)
    '''
    type = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    def __str__(self):
        return "{} : {}".format(self.type, self.value)

    @property
    def robustness(self):
        '''Property. The robustness for type entity type.'''
        robustness = 0
        utt = Utterance.objects.filter(answer__entity__type=self.type)
        if utt.count() > 0:
            for u in utt:
                robustness += u.entity_robustness
            return robustness / utt.count()
        else:
            return 0

    def is_same_entity(self, e):
        '''To compare entity. 2 entities are the same if they have exactly the same value and same type.
        :return boolean, same or not'''
        if self.type == e.type: #and self.value == e.value:
            return True
        else:
            return False


class Strategy(models.Model):
    '''A mutation strategy.
    You can add mutation strategies by:
    - adding a method to the file helpers/mutation_methods.py
    - adding the strategy in the database
    - adding the strategy in the dispatcher in the Utterance class
    '''
    name = models.CharField(max_length=200)
    intent_robustness = models.FloatField(null=True, blank=True)
    def __str__(self):
        return self.name

    @property
    def nb_mut_ans(self):
        '''Property. Number of mutants created with this strategy, that have an answer.'''
        return Mutant.objects.filter(strategy=self, answer__isnull=False).count()

    @property
    def nb_mut_without_ans(self):
        '''Property. Number of mutants created with this strategy, that DON'T have an answer.'''
        return Mutant.objects.filter(strategy=self, answer__isnull=True).count()

    def update_intent_robustness_per_strat(self):
        intents = Intent.objects.all()
        robustness = 0
        for i in intents:
            x = Mutant.objects.filter(answer__intent=i,
                                      utterance__answer__intent=i,
                                      strategy=self).count()
            z = Mutant.objects.filter(utterance__answer__intent=i,
                                      strategy=self,
                                      answer__isnull=False).count()
            if z != 0:
                robustness += (x/z)
        robustness /= intents.count()
        self.intent_robustness = round(robustness, 2)
        self.save()


class Validation(models.Model):
    '''A validation strategy.
    You can add one by:
    - adding a method to the file helpers/validation_methods.py
    - adding a line to the DB
    - adding it in the dispatcher in Utterance class
    '''
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name


class Answer(models.Model):
    '''An answer given by a Natural Language Understanding API.
    Has an intent, and a set of entities.'''
    intent = models.ForeignKey(Intent, null=True, blank=True)
    entity = models.ManyToManyField(Entity, blank=True)
    def __str__(self):
        return "{} {}".format(self.intent.__str__(), self.entity.values_list())


class Utterance(models.Model):
    '''An original query.
    Has a sentence,
    an expected intent (to compute the accuracy of the NLU),
    an answer (might be not computed yet).
    '''
    sentence = models.CharField(max_length=1000)
    expected_intent = models.ForeignKey(Intent, on_delete=models.CASCADE, default=1) # 1 is the pk for "None"
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    entity_robustness = models.FloatField(null=True, blank=True)
    intent_robustness = models.FloatField(null=True, blank=True)

    dispatcher_mutations = {"homophones": mutation_homophones,
                            "swapletter": mutation_swap_letter,
                            "swapword": mutation_swap_word,
                            "random": mutation_random,
                            "verb-end": mutation_verb_at_end,
                            "w2v": mutation_w2v,
                            "glove": mutation_glove}

    dispatcher_validations = {"none": is_valid_true,
                              "google-spell-check": is_valid_spellcheck}

    def __str__(self):
        return self.sentence

    def compute_answer(self):
        '''Compute the answer for this utterance.'''
        if self.answer == None:
            try:
                self.answer = get_answer(self.sentence)
                self.save()
            except KeyError as e:
                self.delete()
                pass

    def mutate(self, strategy, validation, nb):
        '''Create mutants for this utterance, for the given strategy and validation.
        Will create enough mutant to have max "nb" mutants for this utterance.
        :return the number of mutants created
        '''
        strategy_method = self.dispatcher_mutations[strategy.name]
        validation_method = self.dispatcher_validations[validation.name]

        existing_mutants = self.mutant_set.filter(strategy=strategy, validation=validation)

        nb_mutants_created = 0
        nb_mutants_existing = existing_mutants.count()

        if nb_mutants_existing >= nb:
            look_for_mutants = False
        else:
            look_for_mutants = True

        while look_for_mutants:
            new_mutant = strategy_method(self.sentence, existing_mutants)

            if new_mutant == "no mutant":
                look_for_mutants = False
            else:
                if validation_method(self.sentence, new_mutant):
                    m = Mutant(sentence=new_mutant, utterance=self, strategy=strategy, validation=validation)
                    m.save()
                    nb_mutants_created += 1
                    nb_mutants_existing += 1

                if nb_mutants_existing >= nb:
                    look_for_mutants = False

        return nb_mutants_created

    def update_intent_robustness(self):
        '''Robustness on the intent for this utterance.'''
        m_with_good_int = Mutant.objects.filter(utterance=self,
                                     answer__intent=self.answer.intent,
                                     utterance__answer__intent=self.answer.intent).count()
        total_m = Mutant.objects.filter(utterance=self,
                                        utterance__answer__intent=self.answer.intent,
                                        answer__isnull=False).count()
        if total_m == 0:
            self.intent_robustness = 1
        else:
            self.intent_robustness = round(m_with_good_int / total_m, 2)
        self.save()

    def update_entity_robustness(self):
        '''Robustness of the entities for this utterance'''
        if self.mutant_set.count() > 0:
            score = 0
            for m in self.mutant_set.all():
                score += m.entity_robustness
            self.entity_robustness = round(score / self.mutant_set.count(), 2)
        else:
            self.entity_robustness = 1

        self.save()


class Mutant(models.Model):
    '''An utterance that has been modified, using a mutation strategy and a validation strategy.
    '''
    sentence = models.CharField(max_length=1000)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    validation = models.ForeignKey(Validation, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, blank=True, null=True)
    utterance = models.ForeignKey(Utterance, on_delete=models.CASCADE)

    def __str__(self):
        return self.sentence

    def compute_answer(self):
        '''To compute the answer of the mutant.'''
        if self.answer == None:
            try:
                self.answer = get_answer(self.sentence)
                self.save()
            except KeyError as e:
                self.delete()
                pass

    @property
    def entity_robustness(self):
        '''Property. To compute the entity robustness of this mutant.
        Uses the entity comparison method.'''
        score = 0
        if self.utterance.answer.entity.all().count() > 0 and self.answer != None:
            for e1 in self.utterance.answer.entity.all():
                available_entities = [e for e in self.answer.entity.all()]
                for e2 in reversed(available_entities):
                    if e1.is_same_entity(e2):
                        score += 1
                        available_entities.remove(e2)
            return round(score / self.utterance.answer.entity.all().count(), 2)
        else:
            return 1

    @staticmethod
    def nb_mut_i_orig_mutated_to_i_mut(i_orig, i_mut):
        return Mutant.objects.filter(answer__intent=i_orig,
                                     utterance__answer__intent=i_mut).count()

    @staticmethod
    def nb_mut_i_orig(i_orig):
        return Mutant.objects.filter(utterance__answer__intent=i_orig,
                                     answer__isnull=False).count()

    @staticmethod
    def nb_mut_i_mut(i_mut):
        return Mutant.objects.filter(answer__intent=i_mut).count()

    @staticmethod
    def intent_robustness_per_intent(i):
        return Mutant.nb_mut_i_orig_mutated_to_i_mut(i, i) / Mutant.nb_mut_i_orig(i)