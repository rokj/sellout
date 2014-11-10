import logging
from django.db.models.signals import post_save, post_delete
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from django.utils.timezone import now


class Skeleton(models.Model):
    # the 'datetime_deleted' stuff has been removed in favor of a separate table for deleted items
    datetime_created = models.DateTimeField(null=False, blank=True, editable=False, default=now)
    datetime_updated = models.DateTimeField(null=True, blank=True, editable=False, default=now)

    def save(self, *args, **kwargs): 
        """ add datetime_created on first and datetime_updated on each subsequent save """
        if not self.id:
            self.datetime_created = now()
        else:
            self.datetime_updated = now()
        return super(Skeleton, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class SkeletonU(Skeleton):
    """
    Skeleton model with Users included.
    """
    created_by = models.ForeignKey(User, related_name='%(app_label)s_%(class)s_created_by', null=False)
    updated_by = models.ForeignKey(User, related_name='%(app_label)s_%(class)s_updated_by', null=True, blank=True)

    class Meta:
        abstract = True

class Country(models.Model):
    two_letter_code = models.CharField(max_length=2, null=False, primary_key=True)
    name = models.CharField(max_length=64, null=False)
    three_letter_code = models.CharField(max_length=3, null=False)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = _("Countries")