from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from common.models import SkeletonU
from common.functions import get_random_string
from pos.models import Company

import common.globals as g

# length of reference key
REFERENCE_LENGTH = 30


class Action(SkeletonU):
    # company that this action belongs to: can be null if it's a user-only action (like notifications etc.)
    company = models.ForeignKey(Company, null=True, blank=True)

    # the user that's sending the action: can be null if it's generated by the system
    sender = models.EmailField(blank=False, null=False)

    # the user that's to receive the action: can be a registered or non-registered user
    receiver = models.EmailField(blank=False, null=False, db_index=True)

    # action type: invitation, notification, ...
    type = models.CharField(max_length=100, choices=g.ACTION_TYPE_CHOICES, db_index=True, blank=False, null=False)

    status = models.CharField(default=g.ACTION_WAITING, choices=g.ACTION_STATUS_CHOICES, max_length=30, null=False, blank=False)

    # data: any data that will be needed in processing of the action
    data = models.TextField(_("Additional data"))

    # an arbitrary key code associated with this action (like invite accept code etc.)
    reference = models.CharField(_("Reference for an action"),
                                 max_length=REFERENCE_LENGTH, null=False, blank=False, unique=True)

    def __unicode__(self):
        return self.sender + " for " + self.receiver + " : " + self.status + " : " + self.reference

# a pre_save signal: create a reference for any new object
@receiver(pre_save, sender=Action)
def create_reference(sender, instance, *args, **kwargs):
    if not instance.pk:
        # this object hasn't been saved before, create a new reference
        reference = get_random_string(REFERENCE_LENGTH)

        while Action.objects.filter(reference=reference).exists():
            reference = get_random_string(REFERENCE_LENGTH)

        instance.reference = reference