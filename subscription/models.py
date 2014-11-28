import datetime
import json
from django.db import models
from django.db.models import Q
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from action.models import Action
from blusers.models import BlocklogicUser
from common.globals import CANCELED, FIRST_TIME, PAID, FREE, WAITING, SUBSCRIPTION_STATUS
from common.models import SkeletonU
import settings

class Subscriptions(SkeletonU):
    # this class is actually not so important, since it is used only for showing past subscriptions
    # so be more focused on other things when dealing with subscriptions
    subscription = models.ForeignKey('subscription.Subscription', null=False, blank=False)
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=False, blank=False)
    period = models.CharField(null=True, blank=True, default="", max_length=5)
    payment = models.ForeignKey('payment.Payment')
    status = models.CharField(_("Subscription status"), default=WAITING, choices=SUBSCRIPTION_STATUS, max_length=30,
                              null=True, blank=True)

    @staticmethod
    def past_subscriptions(subscription):
        return Subscriptions.objects.filter(subscription=subscription).order_by("end_date")


class Subscription(SkeletonU):
    user = models.ForeignKey(BlocklogicUser, null=True, blank=True, default=None)
    email = models.EmailField(_("Subscription can be also paid for email"), null=True, blank=True, default="")
    days_left = models.IntegerField(null=False, blank=False, default=0)
    days_left_last_decrement = models.DateTimeField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            subscription = Subscription.objects.get(id=self.pk)

            if subscription.days_left == 0 and self.days_left > 0:
                self.start_date = datetime.datetime.now().date()
        else:
            self.start_date = datetime.datetime.now().date()

        super(Subscription, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('user', 'email',)

    def __unicode__(self):
        if self.user is not None:
            return u'%s %s -> %s' % (self.user.first_name, self.user.last_name, self.days_left)
        else:
            return u'%s -> %s' % (self.email, self.days_left)

    @staticmethod
    def move_from_email_to_user(user):
        try:
            user_subscription = Subscription.objects.get(user=user)
            email_subscription = Subscription.objects.get(email=user.email)

            user_subscription.days_left += email_subscription.days_left
            user_subscription.save()

            email_subscription.delete()
        except Subscription.DoesNotExist:
            pass

    @staticmethod
    def extend_subscriptions(payment):
        for s in payment.subscription.all():
            duration = 31 * int(payment.subscription_duration)

            s.days_left += duration
            s.save()

            # we are being nice. start_date should be set, when we recognize the payment.
            start_date = payment.transaction_datetime

            past_subscriptions = Subscriptions.past_subscriptions(s)

            if len(past_subscriptions) > 0:
                last = len(past_subscriptions)-1
                start_date = past_subscriptions[last].end_date

            end_date = start_date + datetime.timedelta(days=duration)

            subscriptions = Subscriptions(subscription=s, start_date=start_date, end_date=end_date, payment=payment, status="", period=str(payment.subscription_duration), created_by=payment.created_by)
            subscriptions.save()

    @staticmethod
    @transaction.atomic
    def subscribe_for_the_first_time(user, creator=None):
        from payment.models import Payment

        if isinstance(user, BlocklogicUser):
            try:
                subscription = Subscription.objects.get(user=user)

                for p in Payment.objects.filter(status=FIRST_TIME, type=FREE):
                    if subscription in p.subscription.all():
                        return False
            except Subscription.DoesNotExist:
                subscription = Subscription(user=user, days_left=31, created_by=creator)
                subscription.save()

        if isinstance(user, basestring):
            try:
                subscription = Subscription.objects.get(email=user)

                for p in Payment.objects.filter(status=FIRST_TIME, type=FREE):
                    if subscription in p.subscription.all():
                        return False
            except Subscription.DoesNotExist:
                subscription = Subscription(email=user, days_left=31, created_by=creator)
                subscription.save()

        payment = Payment(status=FIRST_TIME, type=FREE, total=0, payment_info=json.dumps({"subscription_duration": 1}), created_by=creator)
        payment.save()

        payment.subscription.add(subscription)
        payment.save()

        start_date = subscription.datetime_created.date()
        end_date = start_date + datetime.timedelta(days=31)

        subscriptions = Subscriptions(subscription=subscription, start_date=start_date, end_date=end_date, payment=payment, status="", period="1", created_by=creator)
        subscriptions.save()

        return True

    @staticmethod
    def is_subscription_over(user):
        over = False

        try:
            subscription = Subscription.objects.get(user=user)
            if subscription.days_left == 0:
                over = True

                try:
                    action = Action.objects.get(_for=user.email, what="subscription_almost_over")
                    action.delete()
                except Action.DoesNotExist:
                    pass

            if over:
                try:
                    action = Action.objects.get(_for=user.email, what="subscription_over")
                except Action.DoesNotExist:
                    action = Action(_for=user.email, what="subscription_over", created_by=user)
                    action.save()
            else:
                try:
                    action = Action.objects.get(_for=user.email, what="subscription_over")
                    action.delete()
                except Action.DoesNotExist:
                    pass

        except Subscription.DoesNotExist:
            pass

    @staticmethod
    def is_subscription_almost_over(user):
        almost_over = False

        try:
            subscription = Subscription.objects.get(user=user)
            if subscription.days_left > 0 and subscription.days_left < 8:
                almost_over = True

            if almost_over:
                try:
                    action = Action.objects.get(_for=user.email, what="subscription_almost_over")
                except Action.DoesNotExist:
                    action = Action(_for=user.email, what="subscription_almost_over", created_by=user)
                    action.save()
            else:
                try:
                    action = Action.objects.get(_for=user.email, what="subscription_almost_over")
                    action.delete()
                except Action.DoesNotExist:
                    pass

        except Subscription.DoesNotExist:
            pass

    def includes_user(self, user):
        if self.created_by == user:
            subscriptions = Subscription.objects.filter(payment=self.payment)

            for s in subscriptions:
                if s.user and s.user == user:
                    return True

        return False

    @property
    def information(self):
        now = datetime.datetime.now()

        if now >= self.start_date and now <= self.end_date:
            return "running"
        elif self.payment.status == CANCELED:
            return "canceled"
        elif self.end_date < datetime.datetime.now().date():
            return "over"
        else:
            return "upcoming"

    @property
    def expiration_date(self):
        now = datetime.datetime.now()
        expiration_date = now + datetime.timedelta(days=self.days_left)

        return expiration_date