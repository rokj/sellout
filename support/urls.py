from django.conf.urls import patterns, url

from support import views as views

urlpatterns = patterns('',

    # search results
    url(r'search', views.search, name='search'),

    # single question/post a comment
    url(r'^question/(?P<question_id>\d?)', views.question, name='question'),

    # post a question
    url(r'ask', views.ask, name='ask'),

    # delete a question
    url(r'delete-question', views.delete_question, name='delete_question'),

    # delete a comment
    url(r'delete-comment', views.delete_comment, name='delete_comment'),

    # vote
    url(r'vote', views.vote, name='vote'),

    # accept an answer
    url(r'accept', views.accept, name='accept'),

    # hide welcome message
    url(r'hide-welcome-message', views.hide_welcome_message, name='hide_welcome_message'),

    # support homepage
    url(r'^(?P<category>[\w\d-]+)?', views.home, name='home'),
)
