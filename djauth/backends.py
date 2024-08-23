# -*- coding: utf-8 -*-

import logging

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q

from djauth.managers import LDAPManager
from django_saml.backends import SamlUserBackend


logger = logging.getLogger('debug_logfile')


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
        logger.debug("groups = ")
        if session_data:
            for group in session_data[settings.LDAP_GROUP_ATTR][0].split(','):
                logger.debug(group)
                #group = group.decode(encoding='utf-8')
                if 'CN=' in group:
                    dc = group.split('CN=')[1]
                grup = ldap_groups.get(dc)
                if grup and grup not in groups:
                    groups.append(grup)
        logger.debug(groups)
        return groups

    def configure_user(self, session_data, user, ignore_fields=None):
        """Custom attribute mapping with groups.

        NOTE: ALL SAML attributes in session_data are arrays, even if there is only one element.
        """
        # Call super() to take care of the simple attribute mapping in SAML_ATTR_MAP
        user = super(OneloginBackend, self).configure_user(session_data, user, ignore_fields=ignore_fields)
        logger.debug("session_data = ")
        logger.debug(session_data)
        args = (session_data, user)
        groups = self.get_groups(*args)
        for group in groups:
            grup = Group.objects.get(name=group)
            grup.user_set.add(user)
        return user


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
        groups = eldap.get_groups(result_data)
        # Get the user record or create one with no privileges.
        cid = result_data[0][1][settings.LDAP_ID_ATTR][0]
        user = User.objects.filter(Q(username__exact=username) | Q(pk=cid)).first()
        if not user:
            # Create a User object.
            user = eldap.dj_create(
                result_data,
                auth_user_pk=settings.LDAP_AUTH_USER_PK,
                groups=groups,
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
