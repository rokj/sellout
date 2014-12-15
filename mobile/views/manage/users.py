from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from common.functions import JsonError, JsonParse
from mobile.views.login import get_user_credentials
from mobile.views.manage.configuration import company_config_to_dict
from pos.models import Company, Permission
from django.utils.translation import ugettext as _
from rest_framework.authtoken.models import Token
from pos.views.manage.company import company_to_dict
from pos.views.terminal import switch_user


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def unlock_session(request, company):
    """
        always returns an ajax response
    """

    cleaned_data = switch_user(request, company)

    if cleaned_data['status'] == 'ok':
        user = cleaned_data['user']

        if not user:
            return JsonError(_("User authentication failed."))

        c = cleaned_data['company']

        token, created = Token.objects.get_or_create(user=user)
        user_credentials = get_user_credentials(user)

        return JsonResponse({'token': token.key,
                             'user': user_credentials,
                             'config': company_config_to_dict(request, c),
                             'company': company_to_dict(c, android=True),
                             'status': "ok"})

    else:
        return JsonResponse(cleaned_data)

