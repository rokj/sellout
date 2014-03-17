# author: nejc jurkovic
# date: 3. 9. 2013
#
# Views for managing POS data: home
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from pos.models import Company
from pos.views.util import has_permission, no_permission_view
import common.globals as g

# TODO