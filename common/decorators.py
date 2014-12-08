from functools import wraps
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _


def login_required(view):
    @wraps(view)
    def decorator(*args, **kwargs):
        request = args[0]

        if request.user.is_authenticated():
            # the user is logged in, check if session is locked for this company
            if kwargs.get('company', None) in request.session.get('locked', []):
                # the session is locked, redirect to 'locked' page
                request.session['original_url'] = request.get_full_path()

                if request.is_ajax():
                    # return ajax message
                    return JsonResponse({
                        'status': 'session_locked',
                        'message': _("This session is locked"),
                        'redirect_url': reverse('pos:locked_session', kwargs=kwargs),
                        'original_url': request.session['original_url'],
                    })
                else:
                    print 'redirect to unlock'
                    # redirect to the unlock screen
                    return HttpResponseRedirect(
                        reverse('pos:locked_session', kwargs=kwargs) +
                        '?next=' + request.session['original_url']
                    )
            else:
                # the user is logged in and session is not locked, pass on
                print 'redirecting to original'
                return view(*args, **kwargs)
        else:  # the user is not logged in
            print 'redirecting to index'
            redirect_url = reverse('web:index') + '/?next=' + request.get_full_path() + '#login'

            if request.is_ajax():
                # return ajax message
                return JsonResponse({
                    'status': 'not_logged_in',
                    'message': _("You are not logged in"),
                    'redirect_url': redirect_url,
                    'original_url': request.get_full_path(),
                })
            else:
                # redirect to
                return HttpResponseRedirect(redirect_url)

    return decorator