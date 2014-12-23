from django.conf.urls import patterns, url

from support import views as views

urlpatterns = patterns('',

    # search results
    url(r'search', views.search, name='search'),

    # FAQ list
    url(r'faq', views.faq, name='faq'),

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

    # support homepage
    url(r'(?P<category>\w+)', views.index, name='index'),
    url(r'$', views.index, name='index'),
)
