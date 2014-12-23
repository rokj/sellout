from django.db import models
from django.utils.translation import ugettext as _
from blusers.models import BlocklogicUser
import parameters as p
from common.models import SkeletonU

from datetime import datetime as dtm
import common.globals as g


class AnswerAbstract(SkeletonU):
    category = models.CharField(_("Category"), max_length=16, choices=p.CATEGORIES, null=False, blank=False)
    title = models.CharField(_("Title"), max_length=64, null=False, blank=False)
    text = models.TextField(_("Question"), null=False, blank=False)

    class Meta:
        abstract = True


# question
class Question(AnswerAbstract):
    author = models.ForeignKey(BlocklogicUser, null=False, blank=False)
    # stuff from AnswerAbstract
    plus = models.IntegerField(_("Up votes"), null=True, default=0)
    minus = models.IntegerField(_("Down votes"), null=True, default=0)
    timestamp = models.DateTimeField(_("Timestamp"), default=dtm.now)

    @property
    def comments(self):
        return Comment.objects.filter(question=self).count()

    def rating(self):
        return self.plus - self.minus

    @property
    def answered(self):
        return Comment.objects.filter(question=self, is_answer=True).exists()

    @property
    def date(self):
        # there is no company, just use the default (first)
        return self.timestamp.strftime(g.DATE_FORMATS[0]['python'])

    @property
    def time(self):
        return self.timestamp.strftime(g.TIME_FORMATS[0]['python'])

    def can_delete(self, user):
        # user must be logged in
        if not user.is_authenticated():
            return False

        # question must be written by this user
        if self.author.id != user.id:
            return False

        # question must not be answered
        if self.answered:
            return False

        # no other user's comments are allowed in order to delete
        if Comment.objects.filter(question=self).exclude(author=user).exists():
            return False

        # ok.
        return True


class Comment(SkeletonU):
    author = models.ForeignKey(BlocklogicUser, null=False, blank=False)
    question = models.ForeignKey(Question, null=False, blank=False)
    text = models.TextField(null=False, blank=False)
    timestamp = models.DateTimeField(_("Timestamp"), default=dtm.now)
    is_answer = models.BooleanField(_("Accepted answer"), null=False, blank=True, default=False)

    @property
    def date(self):
        return self.timestamp.strftime(g.DATE_FORMATS[0]['python'])

    @property
    def time(self):
        return self.timestamp.strftime(g.TIME_FORMATS[0]['python'])

    def can_delete(self, user):
        # user must be logged in
        if not user.is_authenticated():
            return False

        # the comment must be user's
        if self.author.id != user.id:
            return False

        # comment cannot be an accepted answer
        if self.is_answer:
            return False

        # there must be no later comments from other users
        if Comment.objects.filter(timestamp__gt=self.timestamp).exclude(author=user).exists():
            return False

        # ok.
        return True


class Vote(SkeletonU):
    """ collects data on who voted on what question; user can vote only once for each question """
    user = models.ForeignKey(BlocklogicUser, null=False, blank=False)
    question = models.ForeignKey(Question)


class Faq(AnswerAbstract):
    pass
