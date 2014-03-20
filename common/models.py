from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from django.utils.timezone import now

# a custom object manager:
class SkeletonManager(models.Manager):
    """ filter out results that were 'deleted' - their datetime_deleted is not None """
    def get_query_set(self):
        return super(SkeletonManager, self).get_query_set().filter(datetime_deleted=None)
    
    #def delete(self): this method is not called from here (see Skeleton.delete())
    
    def deleted(self, *args, **kwargs):
        """ in case anyone will want to see deleted objects """
        return super(SkeletonManager, self).get_query_set().filter(*args, **kwargs).exclude(datetime_deleted=None)

class Skeleton(models.Model):
    #datetime_created = models.DateTimeField(auto_now=False, auto_now_add=True, null=False, blank=False)
    #datetime_updated = models.DateTimeField(auto_now=True, auto_now_add=True, null=False, blank=False)
    #datetime_deleted = models.DateTimeField(null=True, blank=True)
    # removed auto_now and auto_now_add field attributes: http://stackoverflow.com/questions/1737017/django-auto-now-and-auto-now-add
    datetime_created = models.DateTimeField(null=False, blank=True, editable=False) # editable = false: never show in forms
    datetime_updated = models.DateTimeField(null=True, blank=True, editable=False) # only set updated after first editing - after first save()
    datetime_deleted = models.DateTimeField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs): 
        """ add datetime_created on first and datetime_updated on each subsequent save """
        if not self.id:
            self.datetime_created = now()
        else:
            self.datetime_updated = now()
        return super(Skeleton, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # just set datetime_deleted to now()
        self.datetime_deleted = now()#.replace(tzinfo=timezone('utc'))
        self.save()
    
    objects = SkeletonManager()
    
    class Meta:
        abstract = True

class SkeletonU(Skeleton):
    '''
    Skeleton model with Users included.
    '''
    created_by = models.ForeignKey(User, related_name='%(app_label)s_%(class)s_created_by', null=False)
    updated_by = models.ForeignKey(User, related_name='%(app_label)s_%(class)s_updated_by', null=True, blank=True)

    class Meta:
        abstract = True

class Settings(SkeletonU):
    key = models.CharField(_('Key'), max_length=50, null=False, blank=False, unique=True)
    value = models.CharField(_('Value'), max_length=50)
    description = models.TextField(_('Description'), null=True, blank=True)

    __unicode__ = lambda self: u'%s = %s' % (self.key, self.value)
