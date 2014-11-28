from django.shortcuts import resolve_url
from django.utils.encoding import force_str
from django.contrib.auth.decorators import user_passes_test
from common.functions import redirect_to_subscriptions

import settings

__author__ = 'rokj'

from django.http import JsonResponse
from django.utils.translation import ugettext as _

REDIRECT_FIELD_NAME = 'next'

def opt_arguments(func):
    def meta_wrapper(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            # No arguments, this is the decorator
            # Set default values for the arguments
            return func(args[0])
        else:
            def meta_func(inner_func):
                return func(inner_func, *args, **kwargs)
            return meta_func
    return meta_wrapper

@opt_arguments
def subscription_required(view_func, ajax=False):
    def wrapper(request, *args, **kwargs):
        if request.user is not None and not request.user.subscribed:
            if ajax:
                return JsonResponse({'status': 'not_subscribed', 'message': _("You are not subscribed"), 'redirect_url': redirect_to_subscriptions(ajax=True)})

            return redirect_to_subscriptions()

        return view_func(request, *args, **kwargs)

    return wrapper

@opt_arguments
def company_member(view_func, ajax=False):
    def wrapper(request, *args, **kwargs):
        if request.user is not None and not request.user.subscribed:
            if ajax:
                return JsonResponse({'status': 'not_subscribed', 'message': _("You are not subscribed"), 'redirect_url': redirect_to_subscriptions(ajax=True)})

            return redirect_to_subscriptions()

        return view_func(request, *args, **kwargs)

    return wrapper

def login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None, ajax=False):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated():
                return view_func(request, *args, **kwargs)

            # actually it should be like this
            # login_url = force_str(resolve_url(login_url or settings.LOGIN_URL))
            # but now, we are just using settings login url
            login_url = force_str(resolve_url(settings.LOGIN_URL))

            return JsonResponse({'status': 'not_logged_in', 'message': _("User not logged in."), 'login_url': login_url})
        return _wrapped_view

    if ajax:
        return decorator

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
