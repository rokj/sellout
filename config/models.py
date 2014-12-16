import json
from django.db import models
from common.models import SkeletonU


class UserConfig(SkeletonU):
    from blusers.models import BlocklogicUser
    user = models.ForeignKey(BlocklogicUser)
    
    # all settings are stored in json format
    data = models.TextField(null=False)
    
    def __unicode__(self):
        return str(self.user.id) + ":" + self.app


class CompanyConfig(SkeletonU):
    from pos.models import Company
    company = models.ForeignKey(Company)

    data = models.TextField(null=False)

    def __unicode__(self):
        return str(self.company.id) + ":" + self.app

    @property
    def currency(self):
        data = json.loads(self.data)

        if "pos_currency" in data:
            return data["pos_currency"]

        return ""