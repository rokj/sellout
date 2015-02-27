# -*- coding: utf-8 -*-

import os
from django.db import models
from django.db import connections, connection
from django.db import transaction

from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
import psycopg2
from common.globals import MALE, SEX, TAX_PAYER_CHOICES, NORMAL, LOGIN_TYPES, DIRS

from common.models import SkeletonU, Skeleton

from easy_thumbnails.models import Source, Thumbnail
from config.countries import country_choices, country_by_code
import settings


class BlocklogicUser(AbstractUser, Skeleton):
    User._meta.get_field("username").max_length = 75

    # must be set upon registration ('normal' for normal registration, 'google' for google)
    type = models.CharField(max_length=32, blank=False, null=False, default=NORMAL, choices=LOGIN_TYPES)
    sex = models.CharField(_("Male or female"), max_length=6, default=MALE, choices=SEX, blank=False, null=False)
    password_reset_key = models.CharField(_("Lost password reset key or activation key"), max_length=15, blank=True,
                                          null=True, unique=True)
    country = models.CharField(max_length=2, choices=country_choices, null=True, blank=True)
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
            # if there's no first or last for this user, return the us ername which must exist
            return self.email

    @property
    def country_name(self):
        return country_by_code.get(self.country)

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

    def delete(self, *args, **kwargs):
        cursor = connections['bl_users'].cursor()
        cursor.execute("DELETE FROM users WHERE email = %s", [self.email])
        transaction.commit_unless_managed()

        super(BlocklogicUser, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.username = self.email

        super(BlocklogicUser, self).save(*args, **kwargs)

    @property
    def get_selected_company(self):
        from config.functions import get_user_value

        selected_company = ""

        try:
            selected_company = get_user_value(self, "selected_company")
        except KeyError, Exception:
            pass

        return selected_company

    @property
    def companies(self):
        from pos.models import Permission
        return [p.company for p in Permission.objects.filter(user=self)]

        # from pos.models import Company
        # return Company.objects.all()

    def update_password(self):
        """
        Updates user password in master users DB.

        @return: True, False
        """

        conn = psycopg2.connect("host=" + settings.DATABASES["bl_users"]["HOST"] +
                                " dbname=" + settings.DATABASES["bl_users"]["NAME"] +
                                " user=" + settings.DATABASES["bl_users"]["USER"] +
                                " password=" + settings.DATABASES["bl_users"]["PASSWORD"])
        cursor = conn.cursor()

        cursor.execute("SELECT email, password, data FROM users WHERE email = %s", [self.email])
        result = cursor.fetchone()

        if result and len(result) > 0:
            cursor.execute("UPDATE users SET password = %s, datetime_updated = NOW(), updated_by = %s WHERE email = %s",
                           [self.password, settings.SITE_URL, self.email])

        conn.commit()

    def update_user_profile(self):
        """
        Updates user profile in master users DB.
        """

        cursor = connection.cursor()
        try:
            cursor.callproc('bl_update_user', [self.email, settings.SITE_URL])
        finally:
            cursor.close()

        transaction.commit_unless_managed()



class UserImage(SkeletonU):
    from common.functions import ImagePath

    name = models.CharField(_('Image name'), max_length=100, blank=False, null=False)
    description = models.CharField(_('Image description'), max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to=ImagePath(DIRS['users_image_dir'], "users", "blusers_userimage"), null=False)
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
                    except Exception:
                        pass

    def delete(self, *args, **kwargs):
        self.clean_thumbnail()
        self.image.delete()

        super(UserImage, self).delete(*args, **kwargs)
