from django.db import models
from common.models import SkeletonU

from django.utils.translation import ugettext as _

class Config(SkeletonU):
    keyword = models.CharField(max_length=128, blank=False, null=False)
    value = models.CharField(max_length=1024, blank=True, null=False)
    
class Country(models.Model):
    two_letter_code = models.CharField(max_length=2, null=False, primary_key=True)
    name = models.CharField(max_length=64, null=False)
    three_letter_code = models.CharField(max_length=3, null=False)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = _("Countries")
    
def fill_countries(): # will only be used once
    from countries import country_list 
    for c in country_list:
        country = Country(
                          name=c[0],
                          two_letter_code=c[1],
                          three_letter_code=c[2])
        country.save()

# cleanup: a helper class for files that need to be removed after change in database was made
# file names are stored on any model's pre_save signal
# and files are deleted on Cleanup's post_save signal
class Cleanup(models.Model):
    filename = models.CharField(max_length=256)
    
from django.db.models.signals import post_save
from django.dispatch import receiver
import glob
import os
from settings import MEDIA_ROOT as mr

@receiver(post_save, sender=Cleanup)
def my_handler(**kwargs):
    filenames = Cleanup.objects.all()
    
    for f in filenames:
        for g in glob.glob(f.filename + '*'):
            if os.path.exists(g):
                if mr in g: # do not remove anything outside MEDIA dir
                    os.remove(g)
        f.delete()