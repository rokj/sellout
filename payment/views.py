# -*- coding:utf-8 -*-
import datetime
from django.template.defaultfilters import floatformat
import json
import string

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template_from_string
from django.utils.translation import ugettext as _
from django.template import Context, Template
from django.template import defaultfilters
import re

from blusers.models import BlocklogicUser
from common.globals import WAITING, PAID, CANCELED, APPROVED
from payment.service.Paypal import Paypal
import settings
from subscription.models import Subscription, Subscriptions


