# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.models import User
from djauth.managers import LDAPManager


class LDAPBackend(object):
    """Authenciation backend that hits and LDAP service."""

    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, request, username=None, password=None):
        """Confirm that credentials are valid and deal with user accounts."""
        if not password:
            return None

        # initialise the LDAP manager
        eldap = LDAPManager()
        # works for username and username@domain.com
        username = username.lower()
        username = username.lower().split('@')[0]
        # search for a valid user
        result_data = eldap.search(username, field='cn')
        # If the user does not exist in LDAP, Fail.
        if not result_data:
            return None

        # deal with groups
        roles = []
        ldap_groups = settings.LDAP_GROUPS
        for role in result_data[0][1][settings.LDAP_GROUP_ATTR]:
            if isinstance(role, bytes):
                role = role.decode(encoding='utf-8')
            roll = ldap_groups.get(role.split(',')[0].split(' ')[0][3:])
            if roll and roll not in roles:
                roles.append(roll)

        # Attempt to bind to the user's DN.
        try:
            # Success: The user existed and authenticated.
            l.bind(result_data[0][0], password)
        except Exception:
            # Fail: userame and/or password were invalid
            return None

        # Get the user record or create one with no privileges.
        try:
            user = User.objects.get(username__exact=username)
        except User.DoesNotExist:
            # Create a User object.
            user = l.dj_create(
                result_data,
                auth_user_pk=settings.LDAP_AUTH_USER_PK,
                groups=roles,
            )
            if not user.last_name:
                user.last_name = result_data[0][1]['sn'][0]
                user.first_name = result_data[0][1]['givenName'][0]
                user.save()

        # Success.
        return user

    def get_user(self, user_id):
        """Required for django authentication."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
