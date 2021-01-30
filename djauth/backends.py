# -*- coding: utf-8 -*-


from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
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

        # Attempt to bind to the user's DN.
        try:
            # Success: The user existed and authenticated.
            eldap.bind(result_data[0][0], password)
        except Exception:
            # Fail: userame and/or password were invalid
            return None

        # deal with groups
        roles = eldap.get_groups(result_data)

        # Get the user record or create one with no privileges.
        cid = result_data[0][1][settings.LDAP_ID_ATTR][0]
        user = User.objects.filter(Q(username__exact=username) | Q(pk=cid)).first()
        if not user:
            # Create a User object.
            user = eldap.dj_create(
                result_data,
                auth_user_pk=settings.LDAP_AUTH_USER_PK,
                groups=roles,
            )
        # check for username change:
        if user.username != username:
            user.username = username
            user.save()

        # Success.
        return user

    def get_user(self, user_id):
        """Required for django authentication."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
