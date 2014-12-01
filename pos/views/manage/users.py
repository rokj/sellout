from django.shortcuts import get_object_or_404

from pos.models import Company, Permission
import common.globals as g


def list_users(request, company):
    """ show a list of users and their pins """
    c = get_object_or_404(Company, url_name=company)

    permissions = Permission.objects.filter(company=c)



