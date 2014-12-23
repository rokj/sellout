from django.contrib import admin
from support.models import Question, Comment, Vote, Faq

admin.site.register(Question)
admin.site.register(Comment)
admin.site.register(Vote)
admin.site.register(Faq)
