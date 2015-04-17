from django.forms import forms
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext as _

from common.decorators import login_required
from common.functions import JsonError, has_permission
from pos.models import Company

from common import globals as g

# for creating a temp file on disk and opening it with xlrd
import os
import tempfile
import shutil
from contextlib import contextmanager

# the actual import function
from xlsimport import xls_import, XlsImportError


@contextmanager
def temp_input(file_):
    temp = tempfile.NamedTemporaryFile(delete=False)
    shutil.copyfileobj(file_, temp)
    temp.close()
    yield temp.name
    os.unlink(temp.name)


class FileUploadForm(forms.Form):
    xlsfile = forms.FileField(label=_("Excel file (.xls or .xlsx)"))


@login_required
def import_xls(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions for adding products
    if not has_permission(request.user, c, 'product', 'edit'):
        return JsonError(_("You have no permission to add products"))

    context = {
        'results': None,
        'company': c,
        'title': _("Import Products"),
        'site_title': g.SITE_TITLE
    }

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            with temp_input(request.FILES['xlsfile'].file) as tempfilename:
                try:
                    context['results'] = xls_import(tempfilename, c, request.user)
                except XlsImportError as xe:
                    context['results'] = xe.status
    else:
        form = FileUploadForm()

    context['form'] = form

    return render(request, "importexport/importxls.html", context)