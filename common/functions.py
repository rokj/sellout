import string
from random import choice
from config.functions import get_user_value, InvalidKeyError
import globals as g


def get_random_string(length=8, chars=string.letters + string.digits):
    return ''.join([choice(chars) for _ in xrange(length)])


def get_terminal_url(request):
# future store url: same as this page's, excluding what's after the
    # g.MISC['management_url'] string
    # blocklogic.net/pos/app/register-company >> blocklogic.net/pos/company-name
    full_url = request.build_absolute_uri()
    return full_url[:full_url.rfind(g.MISC['management_url'] + '/')]

def redirect_to_his_company(user, ajax=False):
    group = user.homegroup

    if ajax:
        return reverse('web:home', kwargs={'group_id': group.id, 'section': 'home'})

    return redirect('web:home', group.id, 'home')

def redirect_to_last_used_company(user, ajax=False):
    try:
        last_used_group = get_user_value(user, "last_used_company")

        if last_used_group == -1:
            return redirect_to_his_group(user, ajax)
    except InvalidKeyError:
        return redirect_to_his_group(user, ajax)

    if ajax:
        return reverse('web:home', kwargs={'group_id': last_used_group, 'section': 'home'})

    return redirect('web:home', last_used_group, 'home')