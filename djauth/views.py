from django.template import RequestContext
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY

import django


def loggedout(request, template_name='accounts/logged_out.html'):
    """
    Remove the authenticated user's ID from the request.
    """
    # django auth
    try:
        del request.session[SESSION_KEY]
    except KeyError:
        pass
    try:
        del request.session[BACKEND_SESSION_KEY]
    except KeyError:
        pass
    if hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    # VERSION returns (1, x, x, u'final', 1)
    # hopefully, we will be done using django 1.6 by the time 2.x comes out
    if django.VERSION[1] > 6:
        from django.shortcuts import render
        response = render(request, template_name)
    else:
        from django.shortcuts import render_to_response
        response = render_to_response(
            template_name, context_instance=RequestContext(request)
        )

    return response
