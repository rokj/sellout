from django.db import models
from django.utils.translation import ugettext_lazy as _
from common.globals import WAITING, ACTION_STATUS

from common.models import SkeletonU


class Action(SkeletonU):
    _for = models.EmailField(_("For whom"), blank=False, null=False, db_index=True)
    what = models.CharField(_("For what"), help_text=_("Should be just code"), db_index=True,
                            max_length=100, blank=False, null=False)
    status = models.CharField(_("Waiting action status"), default=WAITING, choices=ACTION_STATUS,
                              max_length=30, null=False, blank=False)
    data = models.TextField(_("Additional data"))
    reference = models.CharField(_("Reference for an action"), max_length=30, null=False, blank=False, unique=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            from common.functions import get_random_string

            reference = get_random_string(30)
            actions = Action.objects.filter(reference=reference)

            while len(actions) > 0:
                reference = get_random_string(30)
                actions = Action.objects.filter(reference=reference)

            self.reference = reference

        super(Action, self).save(*args, **kwargs)



