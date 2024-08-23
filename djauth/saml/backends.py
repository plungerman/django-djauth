# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q

from djauth.managers import LDAPManager
from django_saml.backends import SamlUserBackend


class OneloginBackend(SamlUserBackend):
    """Extends the SamlUserBackend() class so that we can manage users."""

    def authenticate(self, request=None, session_data=None, **kwargs):
        """Handle logging in a user based on SAML data."""
        if session_data is None:
            return None

        username = session_data[settings.SAML_USERNAME_ATTR][0]
        username = self.clean_username(username)
        cid = session_data[settings.SAML_CID_ATTR][0]
        # We must create and configure the user in an atomic transaction because
        #  otherwise, a failed reconfigure could cause unintended behavior with a
        #  new user logging in for the second time.
        with transaction.atomic():
            if settings.SAML_CREATE_USER:
                user, created = User.objects.get_or_create(pk=cid)
                if created or settings.SAML_UPDATE_USER:
                    args = (session_data, user)
                    user = self.configure_user(
                        *args,
                        ignore_fields=None if created else settings.SAML_ATTR_UPDATE_IGNORE
                    )
            else:
                try:
                    user = User.objects.get(pk=cid)
                    if settings.SAML_UPDATE_USER:
                        args = (session_data, user)
                        user = self.configure_user(
                            *args,
                            ignore_fields=settings.SAML_ATTR_UPDATE_IGNORE
                        )
                except UserModel.DoesNotExist:
                    return None
            return user if self.user_can_authenticate(user) else None

    def clean_username(self, username):
        """Return the first part of the email address.

        Example: test@example.com -> test.
        """
        return username.split('@')[0]

    def get_groups(self, session_data, user):
        """Return all of the groups with which a user is associated."""
        groups = []
        ldap_groups = settings.LDAP_GROUPS
        if session_data:
            for group in session_data[settings.LDAP_GROUP_ATTR][0].split(','):
                #group = group.decode(encoding='utf-8')
                if 'CN=' in group:
                    dc = group.split('CN=')[1]
                grup = ldap_groups.get(dc)
                if grup and grup not in groups:
                    groups.append(grup)
        return groups

    def configure_user(self, session_data, user, ignore_fields=None):
        """Custom attribute mapping with groups.

        NOTE: ALL SAML attributes in session_data are arrays, even if there is only one element.
        """
        # Call super() to take care of the simple attribute mapping in SAML_ATTR_MAP
        user = super(OneloginBackend, self).configure_user(session_data, user, ignore_fields=ignore_fields)
        args = (session_data, user)
        groups = self.get_groups(*args)
        for group in groups:
            grup = Group.objects.get(name=group)
            grup.user_set.add(user)
        return user
