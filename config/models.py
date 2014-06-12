from django.db import models
from django.contrib.auth.models import User

from common.models import SkeletonU
from pos.models import Company


class UserConfig(SkeletonU):
    user = models.ForeignKey(User)
    
    # all settings are stored in json format
    data = models.TextField(null=False)
    
    def __unicode__(self):
        return str(self.user.id) + ":" + self.app


class CompanyConfig(SkeletonU):
    company = models.ForeignKey(Company)

    data = models.TextField(null=False)

    def __unicode__(self):
        return str(self.company.id) + ":" + self.app


# cleanup: a helper class for files that need to be removed after change in database was made
# file names are stored on any model's pre_save signal
# and files are deleted on Cleanup's post_save signal
class Cleanup(models.Model):
    filename = models.CharField(max_length=256)
    
from django.db.models.signals import post_save
from django.dispatch import receiver
import glob
import os
from webpos.settings import MEDIA_ROOT as mr

@receiver(post_save, sender=Cleanup)
def cleanup_handler(**kwargs):
    filenames = Cleanup.objects.all()
    
    for f in filenames:
        for g in glob.glob(f.filename):
            if os.path.exists(g):
                if mr in g:  # do not remove anything outside MEDIA dir
                    os.remove(g)
        f.delete()