from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /polls/
    url(r'^$', views.index, name='index'),
    # ex: /polls/5/
    url(r'^manage_utterances/$', views.manage_utterances, name='manage_utterances'),
    url(r'^utterance_answers/$', views.utterance_answers, name='utterance_answers'),
    url(r'^compute_answers/$', views.compute_answers, name='compute_answers'),

    url(r'^create_mutants/$', views.create_mutants, name='create_mutants'),
    url(r'^mutants_answers/$', views.mutants_answers, name='mutants_answers'),

    url(r'^results_stats/$', views.results_stats, name='results_stats'),
    url(r'^results_detailed/$', views.results_detailed, name='results_detailed'),
    url(r'^results_utterance/(?P<utterance_id>[0-9]+)/$', views.results_utterance, name='results_utterance'),
    url(r'^results_strategy/(?P<strategy_id>[0-9]+)/$', views.results_strategy, name='results_strategy'),
]
