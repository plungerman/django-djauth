import ldap

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied

# Constants
LDAP_SERVER = settings.LDAP_SERVER
LDAP_PORT = settings.LDAP_PORT
LDAP_PROTOCOL = settings.LDAP_PROTOCOL
LDAP_BASE = settings.LDAP_BASE
LDAP_USER = settings.LDAP_USER
LDAP_PASS = settings.LDAP_PASS
LDAP_EMAIL_DOMAIN = settings.LDAP_EMAIL_DOMAIN

class LDAPBackend(object):
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        if not password:
            #raise PermissionDenied
            return None
        username = username.lower()
        base = LDAP_BASE
        scope = ldap.SCOPE_SUBTREE
        filter = "(&(objectclass=carthageUser) (cn=%s))" % username
        ret = ['givenName','sn','email']

        # Authenticate the base user so we can search
        try:
            l = ldap.initialize('%s://%s:%s' % (LDAP_PROTOCOL,LDAP_SERVER,LDAP_PORT))
            l.protocol_version = ldap.VERSION3
            l.simple_bind_s(LDAP_USER,LDAP_PASS)
        except ldap.LDAPError:
            return None

        try:
            result_id = l.search(base, scope, filter, ret)
            result_type, result_data = l.result(result_id, 0)
            # If the user does not exist in LDAP, Fail.
            if (len(result_data) != 1):
                return None

            # Attempt to bind to the user's DN.
            # we don't need an "if" statement here.
            # simple_bind will except if it fails, never return a value
            l.simple_bind_s(result_data[0][0],password)

            # The user existed and authenticated.
            # Get the user record or create one with no privileges.
            # Could use get_or_create here, but we don't want to be
            # creating random passwords constantly for no reason.

            # get groups
            group = result_data[0][0].split(',')[1]
            try:
                user = User.objects.get(username__exact=username)
                if not user.last_name:
                    user.last_name = result_data[0][1]['sn'][0]
                    user.first_name = result_data[0][1]['givenName'][0]
                    user.save()
                try:
                    g = Group.objects.get(name__iexact=group[3:])
                    g.user_set.add(user)
                except:
                    return user

            except:
                # Theoretical backdoor could be input right here.
                # We don't want that, so we input an unused random
                # password here. The reason this is a backdoor is because
                # we create a User object for LDAP users so we can get
                # permissions, however we -don't- want them to be able to
                # login without going through LDAP with this user. So we
                # effectively disable their non-LDAP login ability by
                # setting it to a random password that is not given to
                # them. In this way, static users that don't go through
                # ldap can still login properly, and LDAP users still
                # have a User object.

                from random import choice
                import string
                temp_pass = ""
                for i in range(8):
                    temp_pass = temp_pass + choice(string.letters)
                user = User.objects.create_user(username,username + '@%s' % LDAP_EMAIL_DOMAIN,temp_pass)
                user.first_name = result_data[0][1]['givenName'][0]
                user.last_name = result_data[0][1]['sn'][0]
                user.save()
                try:
                    g = Group.objects.get(name__iexact=group[3:])
                    g.user_set.add(user)
                except:
                    pass
            # Success.
            return user

        except ldap.INVALID_CREDENTIALS:
            # Name or password were bad. Fail permanently.
            #raise PermissionDenied
            return None

    def get_user(self, user_id):
        """
        OJO: needed for django auth, don't delete
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
