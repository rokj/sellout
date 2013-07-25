from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.db import transaction
from django.forms import ModelForm

from pos.models import Company

from django.http import HttpResponse
import json

def error(request, message):
    return render(request, 'pos/error.html', {'message':message})

def JSON_stringify(data):
    return json.dumps(data)
    
def JSON_response(data):
    return HttpResponse(JSON_stringify(data), mimetype="application/json")

def JSON_parse(string_data):
    return json.loads(string_data)