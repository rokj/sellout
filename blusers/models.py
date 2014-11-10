import os
import datetime
from dateutil.relativedelta import relativedelta
from django.db import models
from django.db import connections
from django.db import transaction

from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.forms import forms
from django.utils.translation import ugettext_lazy as _
from common.globals import MALE, SEX, ADMIN, MEMBER, NORMAL, LOGIN_TYPES, TAX_PAYER_CHOICES

from common.models import SkeletonU, Skeleton

from easy_thumbnails.models import Source, Thumbnail
import settings


class BlocklogicUser(AbstractUser, Skeleton):
    # must be set upon registration ('normal' for normal registration, 'google' for google)
    type = models.CharField(max_length=32, blank=False, null=False, default=NORMAL, choices=LOGIN_TYPES)
    sex = models.CharField(_("Male or female"), max_length=6, default=MALE, choices=SEX, blank=False, null=False)
    password_reset_key = models.CharField(_("Lost password reset key or activation key"), max_length=15, blank=True,
                                          null=True, unique=True)
    country = models.ForeignKey('common.Country', related_name='%(app_label)s_%(class)s_country', blank=True,
                                null=True)
    images = models.ManyToManyField('UserImage', blank=True, null=True)
    # well, user can be created by itself also, so null=False -> null=True
    created_by = models.ForeignKey('blusers.BlocklogicUser', related_name='%(app_label)s_%(class)s_created_by',
                                   null=True)
    updated_by = models.ForeignKey('blusers.BlocklogicUser', related_name='%(app_label)s_%(class)s_updated_by',
                                   null=True, blank=True)

    # __unicode__ = lambda self:  u'%s %s' % (self.first_name, self.last_name)
    def __unicode__(self):
        if self.first_name or self.last_name:
            return u'%s %s' % (self.first_name, self.last_name)
        else:
            # if there's no first or last for this user, return the username which must exist
            return self.email

    def get_subscribed(self):
        from subscription.models import Subscription

        Subscription.subscribe_for_the_first_time(self, self)

        Subscription.move_from_email_to_user(self)

        try:
            subscription = Subscription.objects.get(user=self)
        except Subscription.DoesNotExist:
            return False

        if subscription.days_left > 0:
            return True

        return False

    subscribed = property(get_subscribed)

    def delete(self, *args, **kwargs):
        cursor = connections['bl_users'].cursor()
        cursor.execute("DELETE FROM users WHERE email = %s", [self.email])
        transaction.commit_unless_managed()

        super(BlocklogicUser, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.username = self.email

        super(BlocklogicUser, self).save(*args, **kwargs)

    def get_homecompany(self):
        from pos.models import Company, CompanyUserRole

        try:
            group_user_role = GroupUserRole.objects.get(user=self, role=ADMIN, created_by=self, homegroup=True)
        except GroupUserRole.DoesNotExist:
            # we create his group
            group = Group(created_by=self)
            group.save()

            group_user_role = GroupUserRole(group=group, user=self, role=ADMIN, created_by=self, homegroup=True)
            group_user_role.save()

            return group

        return group_user_role.group

    homecompany q = property(get_homegroup)

    def get_user_groups(self):
        from group.models import GroupUserRole

        return [g.group for g in GroupUserRole.objects.filter(Q(role__exact=MEMBER) | Q(role__exact=ADMIN), user=self).order_by('group__name')]

    user_groups = property(get_user_groups)


class UserImage(SkeletonU):
    from common.functions import get_image_path

    name = models.CharField(_('Image name'), max_length=100, blank=False, null=False)
    description = models.CharField(_('Image description'), max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to=get_image_path("users", "blusers_userimage"), null=False)
    #image = models.ImageField(upload_to="static/img/users", null=False)
    original_filename = models.CharField(_('Original filename'), max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def save(self):
        if not self.original_filename or len(self.original_filename) == 0:
            self.original_filename = self.image.name

        super(UserImage, self).save()

    # kudos:
    # http://stackoverflow.com/questions/16221381/remove-all-thumbnails-generated-with-easy-thumbnails-django-app
    def clean_thumbnail(self):
        if self.image:
            sources = Source.objects.filter(name=self.image.name)
            if sources.exists():
                for thumb in Thumbnail.objects.filter(source=sources[0]):
                    try:
                        os.remove(os.path.join(settings.MEDIA_ROOT, thumb.name))
                        thumb.delete()
                    except Exception, e:
                        pass

    def delete(self, *args, **kwargs):
        self.clean_thumbnail()
        self.image.delete()

        super(UserImage, self).delete(*args, **kwargs)


class UserProfile(SkeletonU):
    user = models.ForeignKey(BlocklogicUser, unique=True, blank=False, null=False)
    # website = models.URLField(_("Website"), blank=True, null=True)
    # facebook = models.URLField(_("Facebook URL"), blank=True, null=True)

    company_name = models.CharField(_("Company name"), max_length=50, blank=True, null=True)
    company_address = models.CharField(_("Company address"), max_length=70, blank=True, null=True)
    company_postcode = models.CharField(_("Company postcode"), max_length=20, blank=True, null=True)
    company_postname = models.CharField(_("Company postname"), max_length=40, blank=True, null=True)
    company_city = models.CharField(_("Company city"), max_length=40, blank=True, null=True)
    company_country = models.ForeignKey('common.Country', related_name='%(app_label)s_%(class)s_company_country', blank=True, null=True)
    company_tax_id = models.CharField(_("Company tax ID"), blank=True, null=True, max_length=40)
    company_tax_payer = models.CharField(_("Compay tax payer"), choices=TAX_PAYER_CHOICES, blank=True, null=True, max_length=20)
    company_website = models.CharField(_("Website of the company"), blank=True, null=True, max_length=200)

    __unicode__ = lambda self:  u'%s %s' % (self.user.first_name, self.user.last_name)
