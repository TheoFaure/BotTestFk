import copy
import os
import random
import re
import pickle
import unicodedata
from framework.helpers.api_calls import syntax_text, translate_google
from framework.models.homophones import Word
from BotTestFk import settings


#### MUTATION METHODS ####
##########################
# This file contains all the mutation methods.
# Takes as parameter the sentence to mutate, and all the existing
# mutants for this sentence.
# Returns the mutant if it is new.
# If we cannot create any new mutant with this method, returns "no mutant".
##########################


def strip_accents(s):
    '''Removes accents to the sentence s and returns it.'''
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def clean_sentence(sentence):
    '''
    Removes all accents,
    things between parenthesis, brackets,
    special characters except -'?!.,;:
    multiple spaces.
    '''
    sentence = re.sub(r"\xa0", " ", sentence) # delete strange char
    sentence = re.sub(r"\[?[0-9]*\]", "", sentence) # delete number in brackets
    sentence = re.sub(r"(?<=[\.?!])(?=[^0-9])", " ", sentence) # put a space after each point
    sentence = re.sub(r"\([^()]*\)", "", sentence) # delete something between parenthesis
    sentence = re.sub(r"\([^()]*\)", "", sentence) # delete something between parenthesis (in case of nested parenthesis)
    sentence = re.sub(r'œ', 'oe', sentence)
    # sentence = strip_accents(sentence)
    sentence = re.sub(r'[^\w\-\',.:;!?]',' ', sentence) # remove special char except -'?!.,;:
    sentence = " ".join(sentence.split()) # remove multiple spaces
    return sentence


def swap(array, i1, i2):
    '''Swap two indices in an array'''
    a2 = copy.deepcopy(array)
    temp = a2[i1]
    a2[i1] = a2[i2]
    a2[i2] = temp
    return a2


def is_possible_new_mutants_swap_word(sentence, existing_mutants):
    '''Return True if it is possible to create a new mutant with
    the word swapping method'''
    nb_words = len(sentence.split(" "))
    if existing_mutants.count() >= nb_words - 1:
        return False
    else:
        return True


def mutation_swap_word(sentence, existing_mutants):
    '''Create a new mutant with the word swapping method'''
    if not is_possible_new_mutants_swap_word(sentence, existing_mutants):
        return "no mutant"

    while True:
        line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
        line_array = line_formatted.split()
        i1 = random.randint(0, len(line_array) - 1)

        if i1 == len(line_array) - 1:  # If last word, take previous
            i2 = i1 - 1
        else:  # Otherwise, take next
            i2 = i1 + 1

        mutant = " ".join(swap(line_array, i1, i2))  # swap the words
        if mutant not in [a['sentence'] for a in existing_mutants.values('sentence')]:
            return mutant


def position_of_verb(sentence, n):
    '''Give the position of the n-th verb in the sentence'''
    tokens = syntax_text(sentence)
    verb_positions = []
    for i, token in enumerate(tokens):
        if token.part_of_speech == "VERB":
            verb_positions.append(i)

    try:
        return verb_positions[n]
    except IndexError as e:
        return -1


def mutation_verb_at_end(sentence, existing_mutants):
    '''Create a mutant with the verb-at-the-end strategy'''
    index_verb = existing_mutants.count()
    line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
    line_array = line_formatted.split()
    pos_verb = position_of_verb(line_formatted, index_verb)  # Begin mutation

    if pos_verb >= 0 and pos_verb < len(line_array):
        line_array.append(line_array[pos_verb])
        line_array[pos_verb] = ""
        mutant = " ".join(line_array).replace("  ", " ").strip()
        return mutant
    else:
        return "no mutant" # No more verbs, so we cannot create a mutant


def valid_swap_index(line, index):
    '''Tells if the letter at index in the line and the letters before and after
    are letters ([a-zA-Z]).'''
    isletter = re.match(r'[a-zA-Z]', line[index]) is not None
    try:
        previousisletter = re.match(r'[a-zA-Z]', line[index - 1]) is not None
    except Exception as e:
        previousisletter = False

    try:
        nextisletter = re.match(r'[a-zA-Z]', line[index + 1]) is not None
    except Exception as e:
        nextisletter = False

    return isletter, previousisletter, nextisletter


def mutation_swap_letter(sentence, existing_mutants):
    '''Create a mutant with the swapping letter mutation strategy.
    Swaps two adjacents letters.'''
    look_for_mutants = True
    nb_trials = 0
    while look_for_mutants:
        line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
        valid_index = False
        index = 0
        while not valid_index and line_formatted.strip():
            index = random.randint(0, len(line_formatted) - 1)
            isletter, previousisletter, nextisletter = valid_swap_index(line_formatted, index)
            valid_index = (isletter and (previousisletter or nextisletter))

        isletter, previousisletter, nextisletter = valid_swap_index(line_formatted, index)
        if nextisletter:
            swap_index = index+1
        elif previousisletter:
            swap_index = index-1
        else:
            return "no mutant"
        mutant = line_formatted[:min(index, swap_index)] + line_formatted[max(index, swap_index)] + \
                    line_formatted[min(index, swap_index)] + line_formatted[max(index, swap_index)+1:]

        if mutant not in [a['sentence'] for a in existing_mutants.values('sentence')]:
            look_for_mutants = False

        nb_trials += 1
        if nb_trials >= 4:
            return "no mutant"

    return mutant


def mutation_random(sentence, existing_mutants):
    '''Create a mutant with the random mutation strategy.
    This changes a letter with an other letter, randomly.'''
    nb_trials = 0
    look_for_mutants = True
    while look_for_mutants:
        index = random.randint(0, len(sentence) - 1)
        while re.match(r'[a-z]', sentence[index]) is None and sentence.strip():
            index = random.randint(0, len(sentence) - 1)
        letter = random.choice('abcdefghijklmnopqrstuvwxyz')
        mutant = sentence[:index] + letter + sentence[index + 1:]
        if mutant not in [a['sentence'] for a in existing_mutants.values('sentence')]:
            look_for_mutants = False
        nb_trials += 1
        if nb_trials >= 4:
            return "no mutant"

    return mutant


def nth_repl(s, sub, repl, nth):
    '''replace the nth occurence of sub with repl in the sentence s'''
    find = s.find(sub)
    # if find is not p1 we have found at least one match for the substring
    i = find != -1
    # loop util we find the nth or we find no match
    while find != -1 and i != nth:
        # find + 1 means we start at the last match start index + 1
        find = s.find(sub, find + 1)
        i += 1
    # if i  is equal to nth we found nth matches so replace
    if i == nth:
        return s[:find]+repl+s[find + len(sub):]
    return s


def mutation_homophones(sentence, existing_mutants):
    '''Replace a word by one of its homophones'''
    line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
    sentence_words = line_formatted.split()

    nb_existing = existing_mutants.count()
    list_homo_words = [a['word'] for a in Word.objects.values('word')]

    possibilities = []
    nb_possibilities = 0

    for word_index_in_sentence, sentence_word in enumerate(sentence_words):
        if sentence_word in list_homo_words:
            try:
                possibilities_for_this = Word.objects.get(word=sentence_word).homophone.word_set.values('word')
            except Exception as e:
                print(sentence_word, sentence)
                raise e
            array_possibilities = [a['word'] for a in possibilities_for_this if a['word'] != sentence_word]
            for possible_swap in array_possibilities:
                possibilities.append([word_index_in_sentence, sentence_word, possible_swap])

    if nb_existing >= len(possibilities):
        return "no mutant"

    # create homophone with word at index "nb_existing" in the array possibilities
    sentence_words[possibilities[nb_existing][0]] = possibilities[nb_existing][2]
    mutant = " ".join(sentence_words)

    if mutant in [a['sentence'] for a in existing_mutants.values('sentence')]:
        raise ValueError("Fail, the mutant created already exists... bug in homophones creation")

    return mutant


# def mutation_google_translate(sentence, existing_mutants):
#     trans1 = translate_google(sentence, "en", "sp")
#     mutant = translate_google(trans1, "sp", "en")
#     if mutant != sentence and mutant not in existing_mutants:
#         return mutant
#     else:
#         return "no mutant"


def create_embedding_mut(sentence, words, prob_word_swapped=0.6):
    m = []
    for w in sentence:
        if random.random() > prob_word_swapped:
            try:
                if len(words[w])>0:
                    m.append(words[w][random.randint(0, len(words[w])-1)])
            except KeyError:
                m.append(w)
        else:
            m.append(w)
    return " ".join(m)


def mutation_w2v(sentence, existing_mutants):
    sentence_ar = sentence.split(" ")
    words = pickle.load(open(
        '/home/theo/Projects/MuTest/BotTestFk/framework/static/framework/sim_words_GoogleNews_W2V.pickle', 'rb'), encoding='latin1')
    mutant = create_embedding_mut(sentence_ar, words)
    i = 0
    while mutant == sentence_ar and mutant in existing_mutants:
        mutant = create_embedding_mut(sentence_ar, words)
        i += 1
        if i > 9:
            return "no mutant"
    return mutant


def mutation_glove(sentence, existing_mutants):
    sentence_ar = sentence.split(" ")
    words = pickle.load(
        open(os.path.join(settings.PROJECT_PATH,
                          "framework/static/framework/sim_words_glove300.pickle"), "rb"))
    mutant = create_embedding_mut(sentence_ar, words)
    i = 0
    while mutant == sentence_ar and mutant in existing_mutants:
        mutant = create_embedding_mut(sentence_ar, words)
        i += 1
        if i > 9:
            return "no mutant"
    return mutant