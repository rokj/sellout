from django.db import models

from pos.models import Company
# Create your models here.


class Sync(models.Model):
    company = models.ForeignKey(Company)
    action = models.CharField(max_length=20, null=False, blank=False)
    model = models.CharField(max_length=20, null=False, blank=False)  # opisno, kateri model
    object_id = models.IntegerField(null=False)
    seq = models.IntegerField(null=False)  # za vsako firmo se zacne z 0 in se poveca z vsakim updejtom
                                                  # kateregakoli modela, ki mu sledimo s syncom
