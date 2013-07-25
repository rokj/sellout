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
    