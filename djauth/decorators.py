from django.conf import settings
from django.urls import reverse_lazy
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect
from django.utils.decorators import available_attrs
from django.utils.encoding import force_str
from django.shortcuts import resolve_url
from django.contrib.auth import login

from djauth.managers import LDAPManager
from djimix.core.encryption import decrypt
from djimix.core.utils import get_userid
from djtools.utils.users import in_group

from functools import wraps

#import logging
#logger = logging.getLogger('debug_logfile')
#logger.debug('here in neutral zone')


def portal_auth_required(session_var, group=None, redirect_url=None, encryption=False):
    """
    Accepts a @@UserID (FWK_User.ID) value via GET (uid) passed
    from jenzabar portal environment, or fall back to django auth
    so you can sign in automatically from the portal after
    authentication there or sign in via django auth.
    """

    def _portal_auth_required(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def wrapper(request, *args, **kwargs):
            #logger.debug('here in the rappa')
            resolved_redirect_url = force_str(
                resolve_url(redirect_url or reverse_lazy("auth_login"))
            )
            if not request.session.get(session_var):
                #logger.debug('if 1')
                if not request.user.is_authenticated:
                    #logger.debug('if 2')
                    # we want to redirect back to current view URL
                    refer = request.get_full_path()
                    #logger.debug('refer = {}'.format(refer))
                    redirect = '{}?next={}'.format(
                        reverse_lazy("auth_login"), refer
                    )
                    #logger.debug('redirect = {}'.format(redirect))
                    #logger.debug('uid = {}'.format(request.GET.get('uid')))
                    # UserID value from the portal
                    if request.GET.get('uid'):
                        guid = request.GET.get('uid')
                        #logger.debug(guid)
                        if encryption:
                            guid = decrypt(guid)
                        portal_user = get_userid(guid, username=True)
                        # for some reason, email is missing for some users.
                        # ID might be missing for administrative users
                        if portal_user and portal_user[4] and portal_user[5]:
                            uid = int(portal_user[5])
                            # obtain username from email
                            username = portal_user[4].split('@')[0]
                            try:
                                user = User.objects.get(pk=uid)
                            except User.DoesNotExist:
                                user = None
                            if not user:
                                # search for user in LDAP store
                                eldap = LDAPManager()
                                result_data = eldap.search(username, field='cn')
                                groups = eldap.get_groups(result_data)
                                # create a new django user
                                user = eldap.dj_create(
                                    result_data,
                                    auth_user_pk=settings.LDAP_AUTH_USER_PK,
                                    groups=groups,
                                )
                        else:
                            # we could not find a user from portal's UID
                            return HttpResponseRedirect(redirect)
                    else:
                        return HttpResponseRedirect(redirect)
                else:
                    user = request.user
                # lastly, check if user belongs to the optional group
                if group:
                    if not in_group(user, group) and not user.is_superuser:
                        return HttpResponseRedirect(resolved_redirect_url)
                if user:
                    # sign in the user manually
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                    request.session[session_var] = True
                else:
                    # no user
                    return HttpResponseRedirect(redirect)

            return view_func(request, *args, **kwargs)
        return wrapper
    return _portal_auth_required
