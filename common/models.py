from django.db import models
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
    created_by = models.ForeignKey('blusers.BlocklogicUser', related_name='%(app_label)s_%(class)s_created_by', null=False)
    updated_by = models.ForeignKey('blusers.BlocklogicUser', related_name='%(app_label)s_%(class)s_updated_by', null=True, blank=True)

    class Meta:
        abstract = True
