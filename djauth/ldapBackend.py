# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from djauth.LDAPManager import LDAPManager


class LDAPBackend(object):
    """Authenciation backend that hits and LDAP service."""

    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, request, username=None, password=None):
        """Confirm that credentials are valid and deal with user accounts."""
        if not password:
            return None

        username = username.lower()
        # works for username and username@domain.com
        username = username.lower().split('@')[0]

        try:
            # initialise the LDAP manager
            l = LDAPManager()
            # search for a valid user
            result_data = l.search(username, field='cn')
            # If the user does not exist in LDAP, Fail.
            if not result_data:
                return None
            # Attempt to bind to the user's DN.
            # Success: The user existed and authenticated.
            # Fail: throw an exception.
            l.bind(result_data[0][0], password)
            # Get group
            group = None

            # Novell LDAP
            if result_data[0][1].get('carthageFacultyStatus'):
                if result_data[0][1]['carthageFacultyStatus'][0] == 'A':
                    group = 'carthageFacultyStatus'

            if result_data[0][1].get('carthageStaffStatus'):
                if result_data[0][1]['carthageStaffStatus'][0] == 'A':
                    group = 'carthageStaffStatus'

            if result_data[0][1].get('carthageStudentStatus'):
                if result_data[0][1]['carthageStudentStatus'][0] == 'A':
                    group = 'carthageStudentStatus'

            # OneLogin LDAP
            groups = []
            for role in result_data[0][1]['memberOf']:
                groups.append(roles[role])
            # Get the user record or create one with no privileges.
            try:
                user = User.objects.get(username__exact=username)
                if not user.last_name:
                    user.last_name = result_data[0][1]['sn'][0]
                    user.first_name = result_data[0][1]['givenName'][0]
                    user.save()
                try:
                    if group:
                        # add them to their group
                        # or 'except' if they already belong
                        g = Group.objects.get(name__iexact=group)
                        g.user_set.add(user)
                except Exception:
                    return user
            except User.DoesNotExist:
                # Create a User object.
                user = l.dj_create(
                    result_data, auth_user_pk=settings.LDAP_AUTH_USER_PK,
                )

            # Success.
            return user

        except Exception as e:
            # userame or password were bad. fail permanently.
            return None

    def get_user(self, user_id):
        """Required for django authentication."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
