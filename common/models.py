from django.db import models
from datetime import datetime as dtm


class Skeleton(models.Model):
    # the 'datetime_deleted' stuff has been removed in favor of a separate table for deleted items
    datetime_created = models.DateTimeField(null=False, blank=True, editable=False, default=dtm.utcnow)
    datetime_updated = models.DateTimeField(null=True, blank=True, editable=False, default=dtm.utcnow)

    def save(self, *args, **kwargs): 
        """ add datetime_created on first and datetime_updated on each subsequent save """
        if not self.id:
            self.datetime_created = dtm.utcnow()
        else:
            self.datetime_updated = dtm.utcnow()
        return super(Skeleton, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class SkeletonU(Skeleton):
    """
    Skeleton model with Users included.
    """
    created_by = models.ForeignKey('blusers.BlocklogicUser', related_name='%(app_label)s_%(class)s_created_by', null=False)
    updated_by = models.ForeignKey('blusers.BlocklogicUser', related_name='%(app_label)s_%(class)s_updated_by', null=True, blank=True)

    class Meta:
        abstract = True

class TemporaryStorage(Skeleton):
    key = models.CharField(max_length=50, null=False, blank=False, unique=True)
    value = models.TextField(null=False, db_index=True)

    created_by = models.CharField(max_length=40, null=True, blank=True)
    updated_by = models.CharField(max_length=40, null=True, blank=True)